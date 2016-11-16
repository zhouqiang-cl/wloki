require([
    'jquery',
    'loki',
    'util/tab-view',
    'util/datatables',
    'util/paginator',
    'handlebars',
    'moment',
    'jquery-mockjax',
], function($, loki, tabview, datatables, Paginator, Handlebars, moment) {

    /* Mocks */
    /*
    var MOCKS = {};
    $.mockjax({
        url: '/api/privileges/overview',
        responseText: MOCKS.overview,
    });
    */
    /* End Mocks */

    // Store fetched data for this page
    loki.data = {};

    var returnData = function(data) {
        return data.data;
    };

    var fetchOverview = function(callback) {
            return $.ajax({
                url: '/api/privilege/overview',
            });
        },

        fetchUserPrivileges = function() {
            var node_id = loki.getParams().nid;
            return $.ajax({
                url: '/api/privilege/nodes/' + node_id + '/user'
            }).then(returnData);
        },

        renderNodeInfo = function() {
            var node = loki.getCurrentNode();
            $('.node-info .path').html(node.path);
        },

        renderPrivilegeType = function(ptypes, current_ptype) {
            var $select = $('.privilege-type select'),
                option;
            ptypes.forEach(function(pt) {
                option = $('<option value=""></option>');
                option.html(pt.name + ' (' + pt.alias + ')').val(pt.name);
                if (current_ptype == pt.name)
                    option.prop('selected', true);
                $select.append(option);
            });
            if (!current_ptype)
                $select.find('option').eq(0).prop('selected', true);
        },

        getStatusAlias = function(status) {
            switch (status) {
                case 'pending':
                    return '未申请';
                case 'applying':
                    return '申请中';
                case 'approved':
                    return '已批准';
                case 'rejected':
                    return '已拒绝';
                case 'revoked':
                    return '已吊销';
                default:
                    return '&nbsp;';
            }
        },

        privilege_item_template = Handlebars.compile($('#privilege-item-template').html()),
        privilege_placeholder_template = Handlebars.compile($('#privilege-placeholder-template').html()),
        renderUserPrivileges = function(privileges) {
            console.log('user privileges', privileges);
            // var $content = $('.privilege-items .content');
            var $content = $('.privilege-items .content .items'),
                apply_button = $('.privilege-items .fn-apply-modal');

            if (privileges) {
                $content.empty();

                privileges.forEach(function(item) {
                    if (['pending', 'rejected', 'revoked'].indexOf(item.status) > -1) {
                        item.disabled = false;
                    } else if (['applying', 'approved'].indexOf(item.status) > -1) {
                        item.disabled = true;
                    } else {
                        item.status = 'null';
                        item.disabled = true;
                    }

                    var $item = $(privilege_item_template(item));
                    // Attach raw data to input
                    $item.find('input[type=checkbox]').data('data', item);

                    $content.append($item);
                });
                apply_button.show();
            } else {
                apply_button.hide();
                $content.html(privilege_placeholder_template());
            }

            // re-render apply button since privileges changed
            renderApplyButton();
        },

        renderApplyButton = function() {
            // var selected = $('.privilege-items .content input[name=privilege-items]:checked'),
            var selected = $('.privilege-items .content .items input[name=privilege-items]:checked'),
                selected_privileges = [];
            selected.each(function(i) {
                selected_privileges.push(this.value);
            });
            console.log('selected', selected_privileges);

            if (selected_privileges.length) {
                $('.fn-apply-modal').disable(false);
            } else {
                $('.fn-apply-modal').disable(true);
            }
        },

        applyPrivleges = function(privileges) {
            var data = {
                node_id: loki.getCurrentNode().id,
                privilege_type: loki.getParams().ptype,
                privilege_names: privileges,
            };

            return $.ajax({
                url: '/api/privilege/petition/apply',
                type: 'POST',
                data: JSON.stringify(data),
                contentType: 'application/json',
            });
        },

        authorizeAdminPrivilege = function(nid, ptype) {
            if (!nid)
                nid = '1';
            if (!ptype)
                ptype = 'granting';

            return $.ajax({
                url: '/api/privilege/authorize',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    node_id: nid,
                    privilege_type: ptype,
                    privilege_name: 'admin',
                })
            }).then(function(json) {
                console.warn('authorize success', arguments);
                return json;
            }, function(xhr) {
                console.warn('authorize failed!', arguments);
                if (xhr.status > 499)
                    loki.popAjaxError(xhr, this);
                return xhr;
            });
        };


    Handlebars.registerHelper('status_alias', function(v) {
        return getStatusAlias(v);
    });


    loki.ready(function() {
        // Bind events
        $('.privilege-type select').on('change', function() {
            var $this = $(this),
                ptype = $this.val() || undefined;

            loki.route_params({ptype: ptype});
        });

        // $('.privilege-items .content').on('change', 'input', function(e) {
        $('.privilege-items .content .items').on('change', 'input', function(e) {
            renderApplyButton();
        });

        $('.fn-apply-modal').on('click', function() {
            var checked = $('.privilege-items input[type=checkbox]:checked'),
                checked_privileges = [],
                checked_str,
                modal = $('.apply-modal');
            checked.each(function() {
                checked_privileges.push(this.value);
            });
            checked_str = checked_privileges.join(', ');

            loki.data.checked_privileges = checked_privileges;

            modal.find('.body .value').html(checked_str);
            modal.modal();
            $('.apply-modal').modal();
        });

        $('.apply-modal-form').on('submit', function(e) {
            e.preventDefault();
            var checked_privileges = loki.data.checked_privileges || [];
            if (checked_privileges.length === 0) {
                alert("You didn't choose any privilege!");
                return;
            }

            applyPrivleges(checked_privileges).then(function() {
                loki.notify('Apply success');

                // Route to tab 1 and force dispatch, this can make the user table
                // and privilege matrix to refresh
                loki.route_params({tab: 1}, true);

            }, loki.notifyErrorMessage);

            $(this).closest('.modal').modal('hide');
        });

        // Close button for all modals
        $('.fn-close-modal').on('click', function() {
            $(this).closest('.modal').modal('hide');
        });
    });


    loki.defineParamsHandler(function(params) {
        var nid = params.nid,
            ptype = params.ptype;

        // Render node info
        if (nid) {
            if (loki.ptree_loaded) {
                renderNodeInfo();
            } else {
                loki.on('ptree_loaded', renderNodeInfo);
            }
        }

        // Prepare overview & render privilege type
        var overview_promise;

        if (loki.data.overview) {
            overview_promise = $.when(loki.data.overview);
        } else {
            // Fetch overview
            overview_promise = fetchOverview().then(function(data) {
                // Store on loki.data
                loki.data.overview = data;

                // Render Privilege Type
                renderPrivilegeType(data.privilege_types, ptype);

                return data;
            }, loki.notifyAjaxError);
        }

        var privileges_promise;

        if (ptype) {
            var getPrivileges = function(overview, privilege_statuses) {
                    var privileges;
                    // Get privileges
                    overview.privilege_types.forEach(function(pt) {
                        if (pt.name == ptype) {
                            privileges = $.extend(true, [], pt.privileges);
                            return;
                        }
                    });
                    if (!privileges) {
                        alert('Could not get privileges for privilege type ' + ptype);
                        return;
                    }

                    console.log('privilege_statuses', privilege_statuses);
                    if (privilege_statuses) {
                        privileges.forEach(function(i) {
                            var p = privilege_statuses[i.name];
                            if (!p) p = {};
                            // i.status = privilege_statuses[i.name] || 'pending';
                            i.status = p.status || 'pending';
                            if (p.node_statuses) {
                                var extra_desc = '&#10;&#10;节点继承:&#10;';
                                p.node_statuses.forEach(function(n) {
                                    var flag = n.node_path === p.determined_by ? '✔' : ' ';
                                    extra_desc += flag + '	' + n.node_path + ':	' + n.status + '&#10;';
                                });
                                i.description += extra_desc;
                            }
                        });
                    }

                    return privileges;
            };

            if (nid) {
                privileges_promise = $.when(
                        overview_promise,
                        fetchUserPrivileges()
                    ).then(function(overview, user_privilege_types) {
                        var privilege_statuses = {};

                        user_privilege_types.forEach(function(up) {
                            if (up.privilege_type == ptype) {
                                up.privileges.forEach(function(i) {
                                    // privilege_statuses[i.name] = i.status;
                                    var p = privilege_statuses[i.name],
                                        setCurrent = function() {
                                            p.status = i.status;
                                            p.determined_by = up.node_path;
                                        };
                                    if (p === undefined) {
                                        p = {
                                            status: i.status,
                                            determined_by: up.node_path,
                                            node_statuses: [
                                                {
                                                    node_path: up.node_path,
                                                    status: i.status,
                                                }
                                            ]
                                        };
                                        privilege_statuses[i.name] = p;
                                    } else {
                                        if (i.status == 'approved') {
                                            if (p.status == 'approved') {
                                                if (up.node_path.length < p.determined_by.length)
                                                    setCurrent();
                                            } else {
                                                setCurrent();
                                            }
                                        } else {
                                            if (p.status != 'approved') {
                                                if (up.node_path.length > p.determined_by.length) {
                                                    setCurrent();
                                                }
                                            }

                                        }
                                        p.node_statuses.push({
                                            node_path: up.node_path,
                                            status: i.status
                                        });
                                    }
                                });
                                return;
                            }
                        });
                        // console.log('user_privilege_types', user_privilege_types, privilege_statuses);

                        return getPrivileges(overview, privilege_statuses);
                   });
            } else {
                privileges_promise = $.when(overview_promise).then(function(overview) {
                    return getPrivileges(overview);
                });
            }

        } else {
            privileges_promise = $.when(undefined);
        }

        $.when(privileges_promise).then(function(privileges) {
            renderUserPrivileges(privileges, nid);
        });
    });


    var render_with_wrapper = function(data, type, full, meta) {
            // console.log(data, type, full, meta);
            var col_name = meta.settings.aoColumns[meta.col].data;
            data = data || '-';
            return '<div class="col-' + col_name + '">' + data + '</div>';
        },

        moment_now = moment().hours(23).minutes(59).seconds(59),

        set_row_id = function(row, data) {
            var mtime = moment(data.mtime),
                days_duration = moment_now.diff(mtime, 'days'),
                class_name = '';
            if (days_duration === 0) {
                // today
                class_name = 'row-today';
            } else if (days_duration === 1) {
                class_name = 'row-yesterday';
            }
            $(row).attr({
                // id: 'privilege-row-' + data.id,
                'data-id': data.id,
                'class': class_name
            });
        },

        format_title = function(nid, ptype, status_text) {
            var t = '显示';
            if (nid) {
                t += '<b>当前节点</b>';
            } else {
                t += '<b>所有节点</b>';
            }
            if (status_text)
                status_text =  '<b>' + status_text + '</b>';
            else
                status_text = '';

            t += '下' + status_text + '的';
            if (ptype) {
                t += '<b>' + ptype + ' 类别</b>';
            } else {
                t += '<b>所有类别</b>';
            }
            t += '的权限条目';
            return t;
        },

        check_nid = function(nid) {
            if (nid === undefined)
                nid = '1';
            return nid;
        },

        get_privileges_column = function(with_menu) {
            var privilege_row_template = Handlebars.compile($('#privilege-row-template').html()),
                column = {
                    data: 'privileges',
                    render: function(data, type, full, meta) {
                        return privilege_row_template(data);
                    }
                };
            if (with_menu)
                column.className = 'with-menu';
            return column;
        };


    var UserView = tabview.TabView.extend({
        tab_name: 'User',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-1'),
        events: {
        },
        initialize: function() {
            var table_options = {
                columns: [
                    {data: 'node_path', width: '4em', render: render_with_wrapper},
                    {data: 'privilege_type', width: '5em', render: render_with_wrapper},
                    get_privileges_column(),
                    {data: 'ctime', width: '5em', render: render_with_wrapper},
                    {data: 'mtime', width: '5em', render: render_with_wrapper},
                ],
                order: [[3, 'desc']],
                autoWidth: false,
            };
            this.user_dt = datatables.createDataTable(
                this.$el.find('table.user-privileges'), table_options);
        },
        handleParams: function(params) {
            // render table
            this.renderUserPrivilegesTable();
        },

        renderUserPrivilegesTable: function() {
            var view = this,
                dt = view.user_dt;

            dt.displayProcessing();
            view.fetchUserPrivilegesRow().then(function(data) {
                dt.reloadData(data);
                dt.displayProcessing(false);
            }, loki.notifyErrorMessage);
        },

        fetchUserPrivilegesRow: function() {
            return $.ajax({
                url: '/api/privilege/user',
            }).then(returnData);
        }
    });


    var AuditMixin = {
        menu_template: Handlebars.compile($('#privilege-menu-template').html()),

        actOnPrivilege: function(action, data) {
            return $.ajax({
                url: '/api/privilege/petition/' + action,
                type: 'POST',
                data: JSON.stringify(data),
                contentType: 'application/json',
            });
        },

        onClickAction: function(e) {
            e.preventDefault();
            var data,
                view = this,
                $action = $(e.currentTarget),
                $item = $action.closest('.item'),
                $row = $action.closest('tr'),
                action = $action.attr('data-action');

            data = {
                privilege_id: $row.attr('data-id'),
                privilege_name: $item.find('.name').html(),
            };
            // console.log('action', action, data);

            this.processAllDT(true);
            this.actOnPrivilege(action, data).then(
                function(privilege) {
                    // console.log('privilege', privilege);
                    // Manually trigger params dispatch to refresh the content
                    loki.dispatchParams();
                }, function(jqxhr) {
                    console.log('arguments', arguments);
                    if (jqxhr.status > 499) {
                        loki.ajax_error_notify(jqxhr);
                    }

                    var message = 'Access denied, you do not have the required privilege to make this action';
                    loki.notify(message, 'error');

                    view.processAllDT(false);
                });

            this.deactivateMenu($item);
        },

        onClickItem: function(e) {
            var item = $(e.currentTarget),
                menu = item.find('.menu'),
                click_on_menu = $(e.target).closest('.menu').length,
                is_active = item.hasClass('active');
            // console.log('clicked', e.currentTarget, e.target);
            // console.log('click on menu', click_on_menu);

            if (click_on_menu)
                return;

            if (!menu.length) {
                menu = $(this.menu_template());
                item.append(menu);
            }

            if (is_active) {
                // Deactive
                this.deactivateMenu(item);
            } else {
                // Active
                this.activateMenu(item);
            }
        },

        activateMenu: function(item) {
            var menu = item.find('.menu'),
                view = this,
                event_name;
            item.addClass('active');
            menu.addClass('active');

            // Document event
            this.menu_id_counter += 1;
            event_name = 'click.menu-item-' + this.menu_id_counter;
            $(document).on(event_name, function(e) {
                var clicked_item = $(e.target).closest('.privilege-operation-item');

                // console.log('document click menu item', clicked_item);
                if (!clicked_item || clicked_item[0] != item[0]) {
                    view.deactivateMenu(item);

                    $(document).off(event_name);
                }
            });
        },

        deactivateMenu: function(item) {
            var menu = item.find('.menu'),
                view = this;
            item.removeClass('active');
            menu.removeClass('active');
        },
    };


    var AdminView = tabview.TabView.extend($.extend({
        tab_name: 'Admin',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-2'),
        events: {
            'click .privilege-row .item': 'onClickItem',
            'click .privilege-row .item .menu .action': 'onClickAction',
            'change .search-box > input': 'searchAllPrivileges',
        },

        disabled_message: '无访问权限 (请申请 Admin 权限以开启访问)',

        authenticate: function(params) {
            // Authorize admin privilege
            var nid = params.nid,
                ptype = params.ptype;

            return authorizeAdminPrivilege(nid, ptype);
        },

        initialize: function() {
            var table_options,
                view = this;

            // Applying table
            table_options = {
                columns: [
                    {data: 'node_path', width: '4em', render: render_with_wrapper},
                    {data: 'privilege_type', width: '3em', render: render_with_wrapper},
                    {data: 'username', width: '3em', render: render_with_wrapper},
                    get_privileges_column(true),
                    {data: 'ctime', width: '5em', render: render_with_wrapper},
                    {data: 'mtime', width: '5em', render: render_with_wrapper},
                ],
                rowCallback: set_row_id,
                order: [[5, 'desc']],
                autoWidth: false,
            };
            this.applying_dt = datatables.createDataTable(
                this.$el.find('table.applying-privileges'), table_options);

            // All table
            table_options = {
                dom: 'T<"clear">ltr',  // remove `i` because paginator is a replacement
                columns: [
                    {data: 'node_path', width: '4em', render: render_with_wrapper},
                    {data: 'privilege_type', width: '5em', render: render_with_wrapper},
                    {data: 'username', width: '5em', render: render_with_wrapper},
                    get_privileges_column(true),
                    {data: 'ctime', width: '5em', render: render_with_wrapper},
                    {data: 'mtime', width: '5em', render: render_with_wrapper},
                ],
                rowCallback: set_row_id,
                order: [[5, 'desc']],
                autoWidth: false,
            };
            this.all_dt = datatables.createDataTable(
                this.$el.find('table.all-privileges'), table_options);

            // Paginator for all table
            this.all_dt.paginator = new Paginator(
                $('.all-privileges-paginator'),
                function(index) {
                    var params = loki.getParams(),
                        nid = params.nid,
                        ptype = params.ptype;
                    return view.renderAllPrivilegesTable(nid, ptype, index);
                },
                {
                    index: 'index',
                    total: 'count',
                    limit: 'limit',
                    pages: 'pages',
                });

            // Menus
            this.menu_id_counter = 0;
        },

        handleParams: function(params) {
            var nid = params.nid,
                ptype = params.ptype,
                params_state = loki.params_state,
                index;
            // console.log('params_state', params_state);

            if (params_state.nid.changed)
                index = 1;

            this.renderAllPrivilegesTable(nid, ptype, index);

            this.renderApplyingPrivilegesTable(nid, ptype);
        },

        renderApplyingPrivilegesTable: function(nid, ptype) {
            var dt = this.applying_dt;
            // if (!(nid || ptype)) {
            //     dt.clearData();
            //     return;
            // }

            this.$el.find('.applying-title').html(format_title(nid, ptype, '待批准'));

            dt.displayProcessing();

            return this.fetchApplypingPrivileges(nid, ptype).then(function(data) {
                dt.reloadData(data);
                dt.displayProcessing(false);
            });
        },

        renderAllPrivilegesTable: function(nid, ptype, index, username) {
            var dt = this.all_dt;

            this.$el.find('.all-title').html(format_title(nid, ptype, ''));

            if (index === undefined)
                index = dt.paginator.index;

            if (username === undefined)
                username = this.$el.find('.search-box input').val();

            dt.displayProcessing();

            return this.fetchAllPrivileges(nid, ptype, index, username).then(function(data) {
                dt.reloadData(data.data);
                // Render paginator
                dt.paginator.render(data);
                dt.displayProcessing(false);
            });
        },

        fetchApplypingPrivileges: function(nid, ptype) {
            /* ptype could be undefined */
            nid = check_nid(nid);
            return $.ajax({
                url: '/api/privilege/nodes/' + nid,
                data: {
                    type: ptype,
                    status: 'applying'
                }
            }).then(returnData);
        },

        fetchAllPrivileges: function(nid, ptype, index, username) {
            /* ptype could be undefined */
            nid = check_nid(nid);

            // console.log('index', index);
            if (index === undefined)
                index = 1;

            var data = {
                type: ptype,
                limit: 8,
                index: index,
            };
            if (username)
                data.username = username;
            return $.ajax({
                url: '/api/privilege/nodes/' + nid,
                data: data
            });
        },

        processAllDT: function(flag) {
            this.applying_dt.displayProcessing(flag);
            this.all_dt.displayProcessing(flag);
        },

        searchAllPrivileges: function(e) {
            var text = $(e.currentTarget).val();
            console.log('search privileges', e.currentTarget, text);

            var params = loki.getParams(),
                nid = params.nid,
                ptype = params.ptype;
            return this.renderAllPrivilegesTable(nid, ptype, 1, text);
        },

    }, AuditMixin));


    var TokenView = tabview.TabView.extend($.extend({
        tab_name: 'Token',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-3'),
        events: {
            'click .privilege-row .item': 'onClickItem',
            'click .privilege-row .item .menu .action': 'onClickAction',
            'click .fn-show-token-modal': 'showTokenModal',
        },

        disabled_message: '无访问权限 (请申请 Admin 权限以开启访问)',

        initialize: function() {
            // Applying table
            var view = this;
            var table_options = {
                columns: [
                    {data: 'node_path', width: '4em', render: render_with_wrapper},
                    {data: 'privilege_type', width: '3em', render: render_with_wrapper},
                    {data: 'username', width: '6em', render: render_with_wrapper},
                    get_privileges_column(true),
                    {data: 'ctime', width: '5em', render: render_with_wrapper},
                    {data: 'mtime', width: '5em', render: render_with_wrapper},
                ],
                rowCallback: set_row_id,
                order: [[2, 'desc']],
                autoWidth: false,
            };
            this.token_dt = datatables.createDataTable(
                this.$el.find('table.token-privileges'), table_options);

            // Submit event for modal
            $('.token-modal-form').on('submit', function(e) {
                e.preventDefault();
                var o = {};
                $(this).serializeArray().forEach(function(i) {
                    o[i.name] = i.value;
                });

                view.addTokenPrivileges(o.node_id, o.privilege_type, o.token).then(function() {
                    loki.notify('Add token privileges success');

                    // Route to tab 1 and force dispatch, this can make the user table
                    // and privilege matrix to refresh
                    loki.route_params({tab: 3}, true);

                }, loki.notifyErrorMessage);

                $(this).closest('.modal').modal('hide');
            });
        },

        authenticate: function(params) {
            // Authorize admin privilege
            var nid = params.nid,
                ptype = params.ptype;

            return authorizeAdminPrivilege(nid, ptype);
        },

        handleParams: function(params) {
            var nid = params.nid,
                ptype = params.ptype;
            this.renderTokenPrivilegesTable(nid, ptype);
        },

        processAllDT: function(flag) {
            this.token_dt.displayProcessing(flag);
        },

        renderTokenPrivilegesTable: function(nid, ptype) {
            var dt = this.token_dt;

            this.$el.find('.token-title').html(format_title(nid, ptype, 'token'));

            dt.displayProcessing();

            return this.fetchTokenPrivileges(nid, ptype).then(function(data) {
                dt.reloadData(data);
                dt.displayProcessing(false);
            });
        },

        fetchTokenPrivileges: function(nid, ptype) {
            nid = check_nid(nid);
            return $.ajax({
                url: '/api/privilege/nodes/' + nid + '/token',
                data: {
                    type: ptype,
                }
            }).then(returnData);
        },

        showTokenModal: function(e) {
            var modal = $('.token-modal'),
                node = loki.getCurrentNode(),
                node_id = node ? node.id : '',
                node_path = node ? node.path : '',
                params = loki.getParams(),
                privilege_type = params.ptype || '';
            modal.find('input[name="node_id"]').val(node_id);
            modal.find('.v-node_path').html(node_path);
            modal.find('input[name="privilege_type"]').val(privilege_type);
            modal.modal();
        },

        addTokenPrivileges: function(node_id, privilege_type, token) {
            console.log('add token privileges', arguments);
            var data = {
                node_id: node_id,
                privilege_type: privilege_type,
                token: token
            };
            return $.ajax({
                url: '/api/privilege/petition/apply_token',
                type: 'POST',
                data: JSON.stringify(data),
                contentType: 'application/json',
            });
        },

    }, AuditMixin));


    tabview.registerTabViews(UserView, AdminView, TokenView);

    loki.registerAjaxError();
    loki.run();
});
