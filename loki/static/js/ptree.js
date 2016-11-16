require([
    'jquery',
    'loki',
    'util/datatables',
    'util/tab-view',
], function($, loki, datatables, tabview) {
    loki.configure({
        restrict_nodes: true
    });


    servers_ratio_stat = {};

    var permillage_to_percent = function(v) {
        return (v * 100).toFixed(1);
    };


    loki.defineTabParamsHandler(function(params) {
    });


    /* Tab Views */

    var NodeView = tabview.TabView.extend({
        tab_name: 'Node',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-1'),
        events: {
        },

        initialize: function() {
            var view = this;

            $('.fn-add-node-modal').click(function() {
                loki.addNodeModal = $('.add-node-modal').modal();
                $('.add-node-modal .body input').focus();
            });

            $('.add-node-modal .add-node-form').on('submit', function(e) {
                e.preventDefault();

                loki.addNodeModal.modal('hide');
                var node_name = $('.add-node-modal .body input').val(),
                    parent_node = loki.getCurrentNode();

                // Reset input
                $('.add-node-modal .body input').val('');

                if (!parent_node) {
                    loki.notify('could not add node if no parent node selected', "error");
                }

                $.when(
                    view.addNode(parent_node.id, node_name)
                ).then(function(json) {
                    // Notify
                    loki.notify("Node '" + node_name + "' created.", 'info');

                    loki.reloadPTreeThenAffect();
                }).fail(function(xhr) {
                    loki.ajax_error_notify(xhr);
                });

                return false;
            });


            $('.fn-rename-node-modal').click(function() {
                loki.renameNodeModal = $('.rename-node-modal').modal();
                loki.renameNodeModal.find('input').val(loki.getCurrentNode().text).focus();
            });

            $('.rename-node-modal .rename-node-form').on('submit', function(e) {
                e.preventDefault();

                loki.renameNodeModal.modal('hide');

                var node = loki.getCurrentNode(),
                    new_name = $('.rename-node-modal .body input').val();

                $('.rename-node-modal .body input').val('');

                $.when(
                    view.renameNode(node.id, new_name)
                ).then(function(json) {
                    // Notify
                    loki.notify("Node '" + json.data.name + "' renamed.", 'info');

                    loki.reloadPTreeThenAffect();
                }).fail(function(xhr) {
                    loki.ajax_error_notify(xhr);
                });
            });


            $('.fn-move-node-modal').click(function() {
                loki.moveNodeModal = $('.move-node-modal').modal();

                // Init ptree
                loki.fetchPTree(function(data) {
                    var $ptree = $('.move-node-modal .ptree'),
                        jstree = $ptree.jstree(true),
                        currentNode = loki.getCurrentNode();

                    if (jstree) {
                        // Clear selection
                        jstree.deselect_all();

                        // Clear serach
                        $('.move-node-modal .search-input').val('').trigger('fn-clean');

                        // Clear move to
                        $('.move-node-modal .move-to-node').html('');

                        // Disable button
                        $('.fn-move-node').disable();
                    } else {
                        // When select node
                        $ptree.on("select_node.jstree", function (e, data) {
                            // Update text
                            var nodeText = data.node.text + ' (' + data.node.id + ')';
                            $('.move-node-modal .move-to-node').html(nodeText);

                            // Enable button
                            $('.fn-move-node').disable(false);
                        });

                        loki.renderPTree($ptree, data, function() {
                            var jstree = $ptree.jstree(true);

                            // Open root node
                            jstree.open_node('1');

                            // Remove current node
                            if (currentNode) {
                                jstree.delete_node(currentNode.id);
                            }

                            // Search input actions
                            $('.move-node-modal .search-input').on('keyup fn-clean', function() {
                                jstree.search(this.value);
                            });

                        });
                    }

                });
            });

            $('.fn-move-node').click(function () {
                loki.moveNodeModal.modal('hide');

                var node = loki.getCurrentNode(),
                    selected = $('.move-node-modal .ptree').jstree(true).get_selected();
                    pid = selected[0];

                $.when(
                    view.moveNode(node.id, pid)
                ).then(function(json) {
                    // Notify
                    loki.notify("Node '" + json.data.name + "' moved.", 'info');

                    loki.reloadPTreeThenAffect();
                }).fail(function(xhr) {
                    loki.ajax_error_notify(xhr);
                });
            });


            $('.fn-delete-node').click(function() {
                var node = loki.getCurrentNode(),
                    node_text = node.text,
                    parent_id = node.parent_id;

                if (!confirm('是否删除?'))
                    return;

                $.when(
                    view.deleteNode(node.id)
                ).then(function (json) {
                    // Notify
                    loki.notify("Node '" + node_text + "' deleted.", 'info');

                    loki.ptree_loaded = false;
                    loki.route_params({nid: parent_id});
                }).fail(function(xhr) {
                    loki.ajax_error_notify(xhr);
                });
            });


            $('.fn-add-contacter-modal').click(function() {
                loki.addContacterModal = $('.add-contacter-modal').modal();
            });

            $('.fn-add-contacter').click(function() {
                loki.addContacterModal.modal('hide');
                var contacter = $('.add-contacter-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.add-contacter-modal > .body > input').val('');

                $.when(
                    view.addContacter(node.id, contacter)
                ).then(function(json) {
                    view.renderNodeDetail(node.id);
                    // Notify
                    //loki.notify("Node " + node.id + "'s owner is/are " + contacter, 'info');
                });
            });
        },

        handleParams: function(params) {
            var view = this;
            var add_btn = $('.fn-add-node-modal'),
                rename_btn = $('.fn-rename-node-modal'),
                move_btn = $('.fn-move-node-modal'),
                delete_btn = $('.fn-delete-node'),
                contacter_btn = $('.fn-add-contacter-modal'),
                btns = [add_btn, rename_btn, move_btn, delete_btn, contacter_btn],
                btn;
            if (params.nid) {
                view.renderNodeDetail(params.nid);

                btns.forEach(function(btn) {
                    btn.disable(false);
                });

                // Restrict add node level
                if (params.nid == '1') {
                    move_btn.disable();
                    delete_btn.disable();
                }
            } else {
                btns.forEach(function(btn) {
                    if (!btn.prop('disabled'))
                        btn.disable();
                });
            }
        },

        renderNodeDetail: function(nid) {
            $.ajax({
                url: '/api/nodes/' + nid
            }).then(function(json) {

                var dl = $('.node-detail > .content dl'),
                    node = json.data;
                $(["id", "name", "dir", "contacter"]).each(function(idx, key){
                    dl.find(".k-"+key).html("");
                    dl.find(".k-"+key).html(node[key]);
                });
                var ph = $('.node-detail > .content .placeholder');
                if (ph.is(':visible')) {
                    ph.fadeOut(200, function() {
                        dl.fadeIn(200);
                    });
                }
            });
        },

        addNode: function(parent_id, name) {
            var data = {
                    parent_id: parent_id,
                    name: name
                },
                aj = $.ajax({
                    url: '/api/nodes',
                    type: 'POST',
                    data: data
                });
            return aj;
        },

        addContacter: function(node_id, contacter) {
            var data = {
                    "node_id": node_id,
                    "contacter": contacter
                },
                aj = $.ajax({
                    url: '/api/nodes/contacter',
                    type: 'POST',
                    data: data
                });
            return aj;
        },

        renameNode: function(node_id, new_name) {
            var aj = $.ajax({
                url: '/api/nodes/' + node_id,
                type: 'POST',
                data: {
                    name: new_name
                }
            });
            return aj;
        },

        moveNode: function(node_id, parent_id) {
            var aj = $.ajax({
                url: '/api/nodes/' + node_id,
                type: 'POST',
                data: {
                    pId: parent_id
                }
            });
            return aj;
        },

        deleteNode: function (node_id) {
            var aj = $.ajax({
                url: '/api/nodes/' + node_id,
                type: 'DELETE'
            });
            return aj;
        },

    });


    var ServerView = tabview.TabView.extend({
        tab_name: 'Server',
        ptree_config: {
            mode: 'enable',
            levels: [-1]
        },
        $el: $('#tab-2'),
        events: {
        },

        initialize: function() {
            var view = this;
            var tabletools_config = {
                "sRowSelect": "os",  // or 'multi'
                "aButtons": [
                    {
                        sExtends: 'select_none',
                        sButtonText: '取消选择'
                    }
                ]
            };

            // Tables
            if (!loki.nodeServersTable) {
                loki.nodeServersTable = datatables.createDataTable(
                    $('.node-servers table'),
                    {
                        columns: [
                            {data: 'hostname'},
                            {
                                data: 'traffic_ratio',
                                render: function(data, type, row, meta) {
                                    var s = data;
                                    if (data === 0) {
                                        s = '0% (IGNORE)';
                                    } else if (data === null) {
                                        s = permillage_to_percent(servers_ratio_stat.auto_value) + '% (AUTO)';
                                    } else {
                                        s = permillage_to_percent(data) + '%';
                                    }
                                    return s;
                                }
                            }
                        ],
                        tableTools: tabletools_config
                    },
                    $('.node-servers .fn-search')
                );
            }
            if (!loki.availableServersTable) {
                loki.availableServersTable = datatables.createDataTable(
                    $('.free-servers table'),
                    {
                        columns: [
                            {data: 'hostname'},
                            {
                                data: 'idc_ids',
                                render: function(data, type, row, meta) {
                                    return data.length;
                                }
                            }
                        ],
                        tableTools: tabletools_config
                    },
                    $('.free-servers .fn-search')
                );
            }

            // Events
            $('.node-servers').on('click', 'tr,.DTTT_button', function() {
                var selected = loki.nodeServersTable.rows('.selected').data();
                if (selected.length) {
                    $('.fn-remove-servers').disable(false);
                    $('.fn-show-traffic-ratio-modal').disable(false);
                } else {
                    $('.fn-remove-servers').disable();
                    $('.fn-show-traffic-ratio-modal').disable();
                }
            });

            $('.free-servers').on('click', 'tr,.DTTT_button', function() {
                var selected = loki.availableServersTable.rows('.selected').data();
                if (selected.length) {
                    $('.fn-add-servers').disable(false);
                } else {
                    $('.fn-add-servers').disable();
                }
            });

            var disableButtons = function() {
                $('.fn-add-servers').disable();
                $('.fn-remove-servers').disable();
                $('.fn-show-traffic-ratio-modal').disable();
            };

            // Buttons
            $('.fn-add-servers').click(function() {
                var dt = loki.availableServersTable,
                    rows = dt.rows('.selected').data(),
                    hostnames = [],
                    node = loki.getCurrentNode(),
                    btn = $(this);

                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    hostnames.push(row.hostname);
                }

                disableButtons();
                view.addServers(node, hostnames);
            });

            $('.fn-remove-servers').click(function() {
                var dt = loki.nodeServersTable,
                    rows = dt.rows('.selected').data(),
                    node = loki.getCurrentNode(),
                    hostnames = [],
                    btn = $(this);

                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    hostnames.push(row.hostname);
                }

                disableButtons();
                view.removeServers(node, hostnames);
            });

            $('.fn-show-traffic-ratio-modal').on('click', function() {
                var modal = $('.traffic-ratio-modal'),
                    dt = loki.nodeServersTable,
                    rows = dt.rows('.selected').data(),
                    server_ids = [],
                    current_ratio = '',
                    current_ratio_sum = 0,
                    $hostnames = modal.find('.hostnames');

                // Change hostnames
                $hostnames.empty();
                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    server_ids.push(row.id);
                    if (row.traffic_ratio !== null)
                        current_ratio_sum += Number(row.traffic_ratio);
                    // console.log('row', row);
                    $hostnames.append(
                        '<span>' + row.hostname + '</span>'
                    );
                }

                if (rows.length == 1) {
                    current_ratio = rows[0].traffic_ratio;
                    if (current_ratio !== null)
                        current_ratio = permillage_to_percent(Number(current_ratio));
                }

                // Change max
                var max = Number(
                    permillage_to_percent(
                        (1 - servers_ratio_stat.explict_sum + current_ratio_sum) / server_ids.length
                    )
                );
                modal.find('input[type=range]').attr('max', max).val(current_ratio);
                modal.find('.max').html(max);
                modal.find('input[type=number]').attr('max', max).val(current_ratio);

                // Store server_ids
                servers_ratio_stat.server_ids = server_ids;

                loki.traffic_ratio_modal = modal.modal();
            });

            $('.traffic-ratio-modal').on('input', 'input[type=range]', function() {
                var range_input = $(this),
                    number_input = $(this).parent().parent().find('input[type=number]');
                number_input.val(range_input.val());
            });

            $('.traffic-ratio-form').on('submit', function(e) {
                e.preventDefault();

                var percent_ratio = loki.traffic_ratio_modal.find('input[type=number]').val(),
                    permillage_ratio = percent_ratio === '' ? null : (Number(percent_ratio) / 100).toFixed(3).toString(),
                    node = loki.getCurrentNode();

                loki.traffic_ratio_modal.modal('hide');
                disableButtons();
                view.updateServersTrafficRatio(node, servers_ratio_stat.server_ids, permillage_ratio);
            });

            $('.fn-show-paste-modal').click(function() {
                loki.pasteModal = $('.paste-modal').modal();
            });

            $('.fn-paste-servers').click(function(){
                var textarea = $(".paste-modal > .body > textarea"),
                    _hostnames = textarea.val().split('\n'),
                    hostnames = [],
                    node = loki.getCurrentNode(),
                    i = 0;

                for(; i < _hostnames.length; i++) {
                    var hostname = _hostnames[i].strip();
                    if (hostname)
                        hostnames.push(hostname);
                }

                loki.pasteModal.modal('hide');
                textarea.val('');
                view.addServers(node, hostnames);
            });

            if(typeof(String.prototype.strip) === "undefined") {
                String.prototype.strip = function() {
                    return String(this).replace(/^\s+|\s+$/g, "");
                };
            }
        },

        handleParams: function(params) {
            var view = this;
            var node = loki.getCurrentNode();
            if (!node)
                return;
            /*
            loki.ptree_promise.then(function() {
                var node = loki.getCurrentNode(),
                    view = loki.tab_views.Server;
                console.log('tab views', view, node);
                if (!node || !view)
                    return;

                console.info('ENABLE DISABLE TAB', node.state.disabled, node);

                if (!node.state.disabled) {
                    view.enableTab();
                } else {
                    view.disableTab('仅允许在最下层节点管理机器');
                }
            });
            */

            if (!node.state.disabled) {
                console.log('valid node, render servers');
                view.renderNodeServers(params.nid);
                if (loki.availableServersTable.nid != params.nid)
                    view.renderAvailableServers(params.nid);
                view.enableTab();
            } else {
                console.log('invalid node, clean UI');
                // loki.nodeServersTable.clearData();
                // loki.availableServersTable.clearData();
                // loki.availableServersTable.nid = null;
                view.disableTab('仅允许在最下层节点管理机器');
            }
        },

        renderNodeServers: function(node_id) {
            var dt = loki.nodeServersTable,
                query = {
                    type: 'node',
                    node_id: node_id
                },
                jqxhr;

            dt.displayProcessing();

            jqxhr = $.ajax({
                url: '/api/servers',
                data: query,
                type: 'GET'
            }).then(function(json) {
                // Update explict_ratio
                var stat = servers_ratio_stat;
                stat.explict_sum = 0;
                stat.null_count = 0;
                json.data.forEach(function(i) {
                    var ratio = i.traffic_ratio;
                    if (ratio === null) {
                        stat.null_count += 1;
                    } else {
                        // Because traffic_ratio is originally string for python - json - js
                        // compatibility
                        ratio = Number(ratio);
                        stat.explict_sum += ratio;
                    }
                });
                stat.auto_value = ((1 - stat.explict_sum) / stat.null_count).toFixed(3);

                console.log('ratio stat', stat);

                dt.reloadData(json.data);
                dt.displayProcessing(false);
            });

            return jqxhr;
        },

        renderAvailableServers: function(node_id) {
            var dt = loki.availableServersTable,
                query = {
                    type: 'available',
                    node_id: node_id
                },
                jqxhr;

            dt.displayProcessing();

            jqxhr = $.ajax({
                url: '/api/servers',
                type: 'GET',
                data: query
            }).then(function(json) {
                dt.reloadData(json.data);
                dt.displayProcessing(false);
                dt.nid = node_id;
            });

            return jqxhr;
        },

        addServers: function(node, hostnames) {
            var view = this;
            if (node.level < 3) {
                alert('node level is less than 3!');
                return false;
            }

            var data = {
                    hostnames: hostnames
                },
                defer = $.Deferred();

            $.ajax({
                url: '/api/nodes/' + node.id + '/servers',
                method: 'PUT',
                data: JSON.stringify(data),
                success: function() {
                  loki.notify("servers added successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            }).always(function() {
                $.absoluteWhen(
                    view.renderNodeServers(node.id),
                    view.renderAvailableServers(node.id)
                ).then(function() {
                    defer.resolve();
                });
            });

            return defer;
        },

        removeServers: function(node, hostnames) {
            var view = this;
            if (node.level < 3) {
                alert('node level is less than 3!');
                return false;
            }

            var data = {
                    hostnames: hostnames
                },
                defer = $.Deferred();

            $.ajax({
                url: '/api/nodes/' + node.id + '/servers',
                method: 'DELETE',
                data: JSON.stringify(data),
                success: function() {
                  loki.notify("servers removed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            }).always(function() {
                $.absoluteWhen(
                    view.renderNodeServers(node.id),
                    view.renderAvailableServers(node.id)
                ).then(function() {
                    defer.resolve();
                });
            });

            return defer;
        },

        updateServersTrafficRatio: function(node, server_ids, ratio) {
            // if (node.level < 3) {
            //     alert('node level is less than 3!');
            //     return false;
            // }
            var view = this;

            var data = {
                    server_ids: server_ids,
                    traffic_ratio: ratio
                },
                defer = $.Deferred();

            $.ajax({
                url: '/api/nodes/' + node.id + '/servers',
                method: 'POST',
                data: JSON.stringify(data),
                success: function() {
                  loki.notify("servers update traffic ratio success");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            }).always(function() {
                $.absoluteWhen(
                    view.renderNodeServers(node.id)
                ).then(function() {
                    defer.resolve();
                });
            });

            return defer;
        },

    });


    var DomainView = tabview.TabView.extend({
        tab_name: 'Domain',
        ptree_config: {
            mode: 'disable',
            levels: [-1]
        },
        $el: $('#tab-3'),
        events: {
        },

        initialize: function() {
            /*
            if (!loki.nodeUrlsTable) {
                loki.nodeUrlsTable = createDataTable(
                    $('.node-urls table'),
                    [
                        {data: 'domain'},
                        {data: 'path'}
                    ],
                    $('.node-urls .fn-search')
                );
            }
            */
            $("#add_url_btn").click(function() {
                var node = loki.getCurrentNode(),
                    node_id = node.id,
                    domain = $("#domain").val(),
                    path = $("#path").val();
                if (!(domain && path && node_id)) {
                    loki.notify("input domain & path & select a node", "error");
                } else {
                    $.ajax({
                        url: "/api/nodes/"+node_id+"/domains",
                        type: "POST",
                        data: JSON.stringify({
                            domain: domain,
                            path: path
                        }),
                        dataType: "json",
                        success: function(data){
                            renderDomains(node.id);
                            loki.notify("add domain succeed");
                            $("#domain").val("");
                            $("#path").val("");
                        },
                        error: function(data) {
                            loki.ajax_error_notify(data);
                        }
                    });
                }
            });

            $('#delete_domain_btn').on('click', function() {
                var node = loki.getCurrentNode(),
                    domain_id = $("#domain_select option:selected")[0].value;
                $.ajax({
                    url: "/api/nodes/"+node.id+"/domains/"+ domain_id,
                    type: 'DELETE',
                    success: function(json) {
                        loki.notify("delete domain succeed");
                        renderDomains(node.id);
                    }
                });
            });
        },

        handleParams: function(params) {
            var view = this;

            if (params.nid) {
                view.renderDomains(params.nid);
            }
        },

        renderDomains: function(node_id) {
            $.ajax({
                url: "/api/nodes/"+node_id+"/domains"
            }).then(function(json) {
                var $domains = $('#domain_select');
                $domains.empty();

                $.each(json.data, function(i, o) {
                    var _str = o.domain + o.path,
                        _id = o.id;
                    $domains.append("<option value='"+ _id +"'>"+ _str +"</option>");
                });
            });
        },

    });


    var UpstreamView = tabview.TabView.extend({
        tab_name: 'Upstream',
        ptree_config: {
            mode: 'disable',
            levels: [-1]
        },
        $el: $('#tab-4'),
        events: {
        },

        initialize: function() {
            var view = this;

            $('.fn-change-name-modal').click(function() {
                loki.changeNameModal = $('.change-name-modal').modal();
            });

            $('.fn-change-name').click(function() {
                loki.changeNameModal.modal('hide');
                var name = $('.change-name-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.change-name-modal > .body > input').val('');

                $.when(
                    view.changeName(node.id, name)
                ).then(function(json) {
                    view.renderUpstreamDetail(node.id);
                });
            });

            $('.fn-change-port-modal').click(function() {
                loki.changePortModal = $('.change-port-modal').modal();
            });

            $('.fn-change-port').click(function() {
                loki.changePortModal.modal('hide');
                var port = $('.change-port-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.change-port-modal > .body > input').val('');

                $.when(
                    view.changePort(node.id, port)
                ).then(function(json) {
                    view.renderUpstreamDetail(node.id);
                });
            });

            $('.fn-change-ip_hash-modal').click(function() {
                loki.changeIphashModal = $('.change-ip_hash-modal').modal();
            });

            $('.fn-change-ip_hash').click(function() {
                loki.changeIphashModal.modal('hide');
                var ip_hash = $('.change-ip_hash-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.change-ip_hash-modal > .body > input').val('');

                $.when(
                    view.changeIphash(node.id, ip_hash)
                ).then(function(json) {
                    view.renderUpstreamDetail(node.id);
                });
            });

            $('.fn-change-isDocker-modal').click(function() {
                loki.changeIsDockerModal = $('.change-isDocker-modal').modal();
            });

            $('.fn-change-isDocker').click(function() {
                loki.changeIsDockerModal.modal('hide');
                var isDocker = $('.change-isDocker-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.change-isDocker-modal > .body > input').val('');

                $.when(
                    view.changeIsDocker(node.id, isDocker)
                ).then(function(json) {
                    view.renderUpstreamDetail(node.id);
                });
            });

            $('.fn-change-publishedPort-modal').click(function() {
                loki.changePublishedPortModal = $('.change-publishedPort-modal').modal();
            });

            $('.fn-change-publishedPort').click(function() {
                loki.changePublishedPortModal.modal('hide');
                var publishedPort = $('.change-publishedPort-modal > .body > input').val(),
                    node = loki.getCurrentNode();

                // Reset input
                $('.change-publishedPort-modal > .body > input').val('');

                $.when(
                    view.changePublishedPort(node.id, publishedPort)
                ).then(function(json) {
                    view.renderUpstreamDetail(node.id);
                });
            });       

            $('.fn-delete-upstream').click(function() {
                var node = loki.getCurrentNode(),
                    node_text = node.text,
                    parent_id = node.parent_id;

                if (!confirm('是否删除?'))
                    return;

                $.when(
                    view.deleteUpstream(node.id)
                ).then(function (json) {
                    // Notify
                    loki.notify("Upstream '" + node_text + "' deleted.", 'info');

                    view.renderUpstreamDetail(node.id);
                });
            });

        },

        handleParams: function(params) {
            var view = this;
            var node = loki.getCurrentNode();
            if (!node)
                return;

            if (node.state.disabled) {
                console.log('invalid node, clean UI');
                view.disableTab('只允许在倒数第二层节点管理 Upstream');
                return;
            }

            var change_name_btn = $('.fn-change-name-modal'),
                change_port_btn = $('.fn-change-port-modal'),
                change_ip_hash_btn = $('.fn-change-ip_hash-modal'),
                change_isDocker_btn = $('.fn-change-isDocker-modal'),
                change_publishedPort_btn = $('.fn-change-publishedPort-modal'),
                delete_upstream = $('.fn-delete-upstream'),
                btns = [change_name_btn, change_port_btn, change_ip_hash_btn, change_isDocker_btn, change_publishedPort_btn, delete_upstream],
                btn;
            if (params.nid) {
                view.renderUpstreamDetail(params.nid);

                btns.forEach(function(btn) {
                    btn.disable(false);
                });

            } else {
                btns.forEach(function(btn) {
                    if (!btn.prop('disabled'))
                        btn.disable();
                });
            }
        },

        renderUpstreamDetail: function(nid) {
            $.ajax({
                url: '/api/nodes/'+nid+"/upstream",
            }).then(function(json) {

                var dl = $('.upstream-detail > .content dl'),
                    upstream = json.data;
                $(["name", "port", "ip_hash", "isDocker", "publishedPort"]).each(function(idx, key){
                    dl.find(".k-"+key).html("");
                    dl.find(".k-"+key).html(upstream[key]);
                });
                var ph = $('.upstream-detail > .content .placeholder');
                if (ph.is(':visible')) {
                    ph.fadeOut(200, function() {
                        dl.fadeIn(200);
                    });
                }
            });
        },

        changeName: function(node_id, name) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/upstream",
                method: 'POST',
                data: JSON.stringify({
                    name: name
                }),
                dataType: "json",
                success: function() {
                  loki.notify("name changed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

        changePort: function(node_id, port) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/upstream",
                method: 'POST',
                data: JSON.stringify({
                    port: port
                }),
                dataType: "json",
                success: function() {
                  loki.notify("port changed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

        changeIphash: function(node_id, ip_hash) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/upstream",
                method: 'POST',
                data: JSON.stringify({
                    ip_hash: ip_hash
                }),
                dataType: "json",
                success: function() {
                  loki.notify("ip_hash changed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

        changeIsDocker: function(node_id, isDocker) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/docker",
                method: 'POST',
                data: JSON.stringify({
                    isDocker: isDocker
                }),
                dataType: "json",
                success: function() {
                  loki.notify("isDocker changed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

        changePublishedPort: function(node_id, publishedPort) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/docker",
                method: 'POST',
                data: JSON.stringify({
                    publishedPort: publishedPort
                }),
                dataType: "json",
                success: function() {
                  loki.notify("publishedPort changed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

        deleteUpstream: function(node_id) {
            var aj = $.ajax({
                url: '/api/nodes/'+node_id+"/upstream",
                method: 'DELETE',
                success: function() {
                  loki.notify("upstream deleted successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            });
            return aj;
        },

    });


    tabview.registerTabViews(NodeView, ServerView, DomainView, UpstreamView);


    loki.registerAjaxError();
    loki.run();
});
