require([
    'jquery',
    'underscore',
    'loki',
    'util/datatables',
    'util/jsform',
    'util/validator',
    'desktop-notify',
    'tinysort',
    // No exports
    'selectize',
    'jsform/servers_checkbox'
], function($, _, loki, datatables, jsform, validator, notify, tinysort) {
    window.tinysort = tinysort;

    loki.configure({
        tabs: {
            '1': 'Template',
            '2': 'Jobset',
            '3': 'Console'
        },
        ptree_config: {
            mode: 'disable',
            levels: [-1]
        },
        restrict_nodes: true
    });


    loki.defineTabInitializers({
        initTemplate: function(params) {
            console.log('init template');
            // Create template table
            var tableOptions = {
                    columns: [
                        {data: 'template_name'},
                        {data: 'type'}
                    ],
                    createdRow: function(row, data, dataIndex) {
                        $(row).attr("id", "id-" + data.template_id);
                    },
                    tableTools: {
                        "sRowSelect": "single",  // or 'multi'
                    }
                },
                templateTable = datatables.createDataTable(
                    $('#template-table'), tableOptions, $('.template-config .fn-search'));
            loki.templateTable = templateTable;

            var getCurrentTemplate = function(){
                var selected = templateTable.rows('.selected').data()[0];
                return selected;
            };
            // Create button
            $('.fn-create-template').click(function() {
                // console.log(policyTable.rows('.selected').data().length);
                templateTable.tt().fnSelectNone();

                showCreateTemplate();
            });

            // On select rows
            $('#template-table').on('click row_select', 'tr', function() {
                var selected = getCurrentTemplate();
                console.log(selected);
                if (selected) {
                    showUpdateTemplate(selected);
                } else {
                    hideTemplateDetail();
                }
            });

            // bind template update submit
            $('.template-detail-form').on("submit", function(e){
                e.preventDefault();

                var data = jsform.serializeForm($(this)),
                    currentTemplate = getCurrentTemplate(),
                    template_id = currentTemplate.template_id,
                    type = currentTemplate.type;

                $.ajax({
                    url: "/api/job/template/" + template_id + "?node_id=" + loki.getCurrentNode().id,
                    data: JSON.stringify({
                        type: type,
                        parameters: data
                    }),
                    type: "POST",
                    dataType: "json",
                    success: function(json) {
                        loki.notify(json.data);
                        renderTemplate(loki.getCurrentNode().id);
                        hideTemplateDetail();
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                })
            });

            // Delete Button on template-detail-form
            $(".template-detail-form button#delete-b").on("click", function(e){
                e.preventDefault();

                if (confirm('yes or no')) {
                    var currentTemplate = getCurrentTemplate(),
                        template_id = currentTemplate.template_id;
                    $.ajax({
                        url: "/api/job/template/" + template_id + "?node_id=" + loki.getCurrentNode().id,
                        type: "DELETE",
                        dataType: "json",
                        success: function() {
                            loki.notify("delete template success");
                            renderTemplate(loki.getCurrentNode().id);
                            hideTemplateDetail();
                        },
                        error: function(e){
                            loki.ajax_error_notify(e);
                        }
                    })
                }
            });

            // Copy button on template detail form
            $('.template-detail-form button#copy-b').click(function() {
                var template = $('.template-detail-form'),
                    values = jsform.serializeForm(template),
                    type = values['type'],
                    base_template_data = getCurrentTemplate().template_data,
                    template_data = [];
                templateTable.tt().fnSelectNone();
                base_template_data.forEach(function (o){
                    var n = $.extend(true, {}, o);
                    if (n.key in values) {
                        if (n.key === "name") {
                            n.value = values[n.key] + " 副本"
                        } else if (n.type == "servers_checkbox") {
                            $.map(n.value, function (node) {
                                if (node.hostname in values[n.key])
                                    node.state = {selected: true}
                            });
                        } else if (n.type == "dictinput") {
                            n.value  = $.map(values[n.key], function(k, v) {
                                return {key: k, v: v}
                            })
                        } else {
                            n.value = values[n.key]
                        }
                    }
                    template_data.push(n)
                });

                showCopyTemplate(type, template_data);
            });

            // bind template create submit
            $('.template-create-form').on("submit", function(e){
                e.preventDefault();
                var data = jsform.serializeForm($(this)),
                    type = data['type'];
                delete data['type'];
                $.ajax({
                    url: "/api/job/template?node_id=" + loki.getCurrentNode().id,
                    data: JSON.stringify({
                        type: type,
                        parameters: data
                    }),
                    type: "PUT",
                    dataType: "json",
                    success: function() {
                        loki.notify("create template success");
                        renderTemplate(loki.getCurrentNode().id);
                        hideTemplateDetail();
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                })
            });

            // bind template create type change
            $('.template-create-form select.template-type').on('change', function(){
                var valueSelected = this.value;
                var content = $('.template-create-form .content');
                content.empty();
                jsform.renderForm(content, loki.templateType[valueSelected]);
            });

            //fetch template type
            //fetchTemplateType();
        },
        initJobset: function(params) {
            // Create collector table
            var tableOptions = {
                    columns: [
                        {data: 'template_name'},
                        {data: 'template_type'}
                    ],
                    tableTools: {
                        "sRowSelect": "single",  // or 'multi'
                    }
                },
                deploymentTable = datatables.createDataTable(
                    $('.template-deployment table'), tableOptions, $('.template-deployment .fn-search'));
            loki.deploymentTable = deploymentTable;

            var getCurrentTemplate = function(){
                var selected = deploymentTable.rows('.selected').data()[0];
                return selected;
            };

            $('#deployment-table').on('click row_select', 'tr', function() {
                var selected = getCurrentTemplate();
                console.log(selected);
                if (selected) {
                    showDeployDetail(selected);
                } else {
                    hideDeployDetail();
                }
            });

            var detail_schema = new validator.Schema({
                servers: {
                    type: Array,
                    length: [1, null],
                    message: '应至少选择一个机器进行发布'
                }
            });

            var $detail_form = $('.deployment-detail-form'),
                $detail_form_errors = $detail_form.find('.errors');
            if (!$detail_form_errors.length) {
                $detail_form_errors = $('<ul></ul>')
                    .addClass('errors alert alert-danger')
                    .hide();
                $detail_form.find('.actions').before($detail_form_errors);
            }

            var show_form_errors = function(errors) {
                $detail_form_errors.empty();
                errors.forEach(function(e) {
                    var $error = $('<li></li>').html(e.message);
                    $detail_form_errors.append($error);
                });
                $detail_form_errors.show();
            };

            $detail_form.on("submit", function(e){
                e.preventDefault();
                $detail_form_errors.hide().empty();

                var data = jsform.serializeForm($(this)),
                    type = data.type,
                    errors = detail_schema.validate(data);

                if (errors && errors.length) {
                    console.warn('errors', errors);
                    show_form_errors(errors);
                    return;
                }
                console.log('data and errors', data, errors);

                // console.log('deployment form errors', errors);

                $.ajax({
                    url: "/api/job/deploy?node_id=" + loki.getCurrentNode().id,
                    data: JSON.stringify({
                        type: type,
                        parameters: data
                    }),
                    type: "PUT",
                    dataType: "json",
                    success: function(json) {
                        loki.notify("create template success");
                        var params = loki.getParams();
                        params.tab = 3;
                        params.rid = json.jobset_id;
                        loki.route('?' + $.param(params));
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                });
            });
        },
        initConsole: function(params) {
            var tableOptions = {
                    columns: [
                        {data: 'name'},
                        {data: 'ctime'},
                        {data: 'status'}
                    ],
                    rowCallback: function(row, data) {
                        $(row).attr('data-id', data.id);
                    },
                    order: [[ 1, "desc" ]],
                    tableTools: {
                        "sRowSelect": "single",  // or 'multi'
                    }
                },
                consoleTable = datatables.createDataTable(
                    $('#console-table'), tableOptions, $('.console .fn-search'));
            loki.consoleTable = consoleTable;

            // On select rows
            $('#console-table').on('click', 'tr', function() {
                var selected = consoleTable.rows('.selected').data();
                    params = loki.getParams();
                if (selected.length) {
                    params.rid = selected[0].id;
                    stopStatusPolling();
                    loki.route('?' + $.param(params));
                } else {
                    delete(params['rid']);
                    stopStatusPolling();
                    loki.route('?' + $.param(params));
                }
            });

            $(".job-servers").on("click", ".console-host .title", function(){
                var title = $(this),
                    host = title.parent(),
                    stop_status = ["succ", "fail"],
                    content = title.next();
                if(_.contains(stop_status, host.attr('data-status'))) {
                    if (content.is(':visible')) {
                        content.hide();
                    } else {
                        var params = loki.getParams(),
                            server = host.attr('data-server'),
                            rid = params.rid;
                        $.ajax({
                            url: '/api/job/get_log?tid='+rid+'&hostname='+server,
                            type: 'GET',
                            dataType: 'json',
                            success: function(json){
                                content.empty();
                                content.html('<pre>'+json.data+'</pre>');
                                content.show();
                            }
                        });
                    }
                }
            });

            $('.fn-pause').on('click', function() {
                var params = loki.getParams(),
                    rid = params.rid;
                press(this);
                $.ajax({
                    url: "/api/job/deploy/pause/"+rid,
                    type: "GET",
                    dataType: "json",
                    success: function(json) {
                        var status = json.status;
                        if (status) {
                            loki.notify("send pause signal succeed");
                        } else {
                            loki.notify("fail to send pause signal", "error")
                        }
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                });
            });

            $('.fn-play').on('click', function() {
                var params = loki.getParams(),
                    rid = params.rid;
                press(this);
                $.ajax({
                    url: "/api/job/deploy/play/"+rid,
                    type: "GET",
                    dataType: "json",
                    success: function(json) {
                        var status = json.status;
                        if (status) {
                            loki.notify("send resume signal succeed");
                        } else {
                            loki.notify("fail to send resume signal", "error")
                        }
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                });
            });

            $('.fn-stop').on('click', function() {
                var params = loki.getParams(),
                    rid = params.rid;
                press(this);
                $.ajax({
                    url: "/api/job/deploy/stop/"+rid,
                    type: "GET",
                    dataType: "json",
                    success: function(json) {
                        var status = json.status;
                        if (status) {
                            loki.notify("send stop signal succeed");
                        } else {
                            loki.notify("fail to send stop signal", "error")
                        }
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                });
            });

            $('.fn-trash').on('click', function() {
                var params = loki.getParams(),
                    rid = params.rid;
                press(this);
                $.ajax({
                    url: "/api/job/deploy/"+rid,
                    type: "DELETE",
                    dataType: "json",
                    success: function() {
                        loki.notify("delete job succeed")
                    },
                    error: function(e){
                        loki.ajax_error_notify(e);
                    }
                });
            });

            loki.on('rid_change', function() {
                stopStatusPolling();

            })
        }
    });


    loki.defineTabHandlers({
        handleTemplate: function(params) {
            // disable create template when rid switching
            $(".fn-create-template").attr("disabled", true);
            if (params.nid) {
                renderTemplate(params.nid);
            }
        },
        handleJobset: function (params) {
            if (params.nid) {
                renderDeployTemplate(params.nid);
            }
        },
        handleConsole: function (params) {
            if (params.nid) {
                renderConsoleTable();
                if (params.rid) {
                    showConsole();
                } else {
                    hideConsole();
                }
            }
        }
    });


    var renderTemplate= function(nid) {
        $.when(
                $.ajax({
                    url: '/api/job/template?node_id='+nid,
                    dataType: "json"
                }),
                // fetch template_type_json
                fetchTemplateType()
            ).then(function(template_json, template_type_json){
                var dt = loki.templateTable;
                console.log(template_type_json[0]);
                if (!dt._inited) {
                    dt.clear();
                }
                dt.rows.add(template_json[0].data);
                dt.draw();
                dt._inited = false;
                // enable create template button
                $(".fn-create-template").attr("disabled", false);
                hideTemplateDetail();
            });
    };

    var showCreateTemplate = function() {
        var el = $('.template-detail');
        el.find('.title').hide();
        el.find('.pure-form').hide();
        el.find('.title.for-create').show();
        el.find('.pure-form.for-create').show();
        var content = $('.template-create-form .content');
        content.empty();
        $("select.template-type").empty();
        for (k in loki.templateType) {
            if (!default_type)
                var default_type = k;
            var option = '<option value="'+ k +'">' + k + '</option>';
            $("select.template-type").append(option);
        }
        jsform.renderForm(content, loki.templateType[default_type]);
        el.show();
    };

    var showCopyTemplate = function (type, template_data) {
        var el = $('.template-detail'),
            option = '<option value="'+ type +'">' + type + '</option>',
            content = $('.template-create-form .content'),
            template_type_select_options = $(".template-create-form select.template-type");
        el.find('.title').hide();
        el.find('.pure-form').hide();
        el.find('.title.for-create').show();
        el.find('.pure-form.for-create').show();
        content.empty();
        template_type_select_options.empty();
        template_type_select_options.append(option);
        jsform.renderForm(content, template_data);
        el.show();
    };

    var showUpdateTemplate= function(selected) {
        var el = $('.template-detail');
        el.find('.title').hide();
        el.find('.pure-form').hide();
        el.find('.title.for-update').show();
        el.find('.pure-form.for-update').show();
        var content = $('.template-detail-form .content');
        content.empty();
        jsform.renderForm(content, selected.template_data);
        el.show();
    };


    var hideTemplateDetail = function() {
        $('.template-detail').hide();
    };


    var renderDeployTemplate = function(nid) {
        $.when(
            $.ajax({
                url: '/api/job/deploy_type?node_id='+nid,
                dataType: "json"
            })
        ).then(function(json){
            var dt = loki.deploymentTable;
            if (!dt._inited) {
                dt.clear();
            }
            dt.rows.add(json.data);
            dt.draw();
            dt._inited = false;
            hideDeployDetail();
        });
    }


    var showDeployDetail = function(selected) {
        var el = $('.deployment-detail');
        var content = $('.deployment-detail-form .content');
        content.empty();
        jsform.renderForm(content, selected.parameters, {style: 'stacked'});
        el.show();
    }


    var hideDeployDetail = function() {
        $('.deployment-detail').hide();
    }


    var renderConsoleTable= function() {
        var params = loki.getParams();
        $.when(
                $.ajax({
                    url: '/api/job/deploy?node_id='+params.nid,
                    dataType: "json"
                })
            ).then(function(json){
                var dt = loki.consoleTable;
                if (!dt._inited) {
                    dt.clear();
                }
                dt.rows.add(json.data);
                dt.draw();
                dt._inited = false;
                if(params.rid){
                    var row = dt.$find('[data-id=' + params.rid + ']');
                    if (!row.length) {
                        loki.notify('No row id ' + params.rid, 'error');
                        return;
                    }
                    // Select row DataTable
                    loki.consoleTable.selectRow(row[0]);
                }
            });
    }


    var renderConsole= function(rid) {
        console.log('render console');
        $.when(
            $.ajax({
                url: '/api/job/deploy/' + rid,
                dataType: "json",
                success: function (json) {
                    $(".job-parameters").empty();
                    $(".job-servers").empty();
                    jsform.renderForm($(".job-parameters"), json.data.parameters);
                    $(json.data.servers).each(function (idx, server) {
                        $(".job-servers").append(
                            '<div class="console-host" data-server="' + server + '">' +
                                '<div class="title" style="cursor:pointer">' + server +
                                    '<span class="float-right server-status"></span>' +
                                '</div>' +
                                '<div class="content" style="display:none;"></div>' +
                            '</div>'
                        );
                    });
                    $(".job-status").text(json.data.status);
                },
                error: function (e) {
                    loki.ajax_error_notify(e);
                }
            })
        ).then(function () {
                getStatusPolling(rid);
            }, function () {
                console.error("render deploy console fail");
            }
        );
    };


    var showConsole = function(rid) {
        var el = $(".console-detail"),
            params = loki.getParams();
        renderConsole(params.rid);
        el.show();
    };


    var hideConsole = function() {
        var el = $(".console-detail");
        el.hide();
    };


    var fetchTemplateType = function() {
        return $.ajax({
            url: "/api/job/template_type?node_id=" + loki.getCurrentNode().id,
            type: "GET",
            dataType: "json",
            success: function(json){
                loki.templateType = json;
            }
        });
    };

    var getStatusPolling = function (rid, version) {
        var poll_flag = true,
            stop_status = ["succ", "fail", "error", "stopped"],
            poll_interval = 0;

        if (!version)
            version = -1;

        loki.pollingRequest = $.ajax({
            url: "/api/job/get_status?tid=" + rid + "&version=" + version,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                if (_.contains(stop_status, data.data.status))
                    poll_flag = false;
                version = data.version;
                renderDeployStatus(rid, data.data);
                poll_interval = 1000;
            },
            error: function (e) {
                if (e.status == 404) {
                    renderDeployStatus(rid);
                } else {
                    loki.ajax_error_notify(e);
                }
                poll_interval = 3000;
            },
            complete: function (jqXHR, status) {
                if (poll_flag && status != "abort") {
                    loki.pollingTimer = setTimeout(function () {
                        getStatusPolling(rid, version)
                    }, poll_interval);
                }
            }
        });
    };

    var stopStatusPolling = function () {
        if (loki.pollingRequest) {
            loki.pollingRequest.abort();
            delete loki.pollingRequest;
        }
        if (loki.pollingTimer) {
            clearTimeout(loki.pollingTimer);
            delete loki.pollingTimer;
        }
    };

    var press = function(btn) {
        console.log($(btn).find(".fa"));
        $(".button-pressed").removeClass("button-pressed");
        $(btn).addClass("button-pressed");
    };

    var STATUS_SEQUENCE = ['paused', 'error', 'fail', 'doing', 'undo', 'succ'],
        get_seq_index = function(i) {
            return STATUS_SEQUENCE.indexOf(i);
        },
        status_count_template = _.template('<span>pending:&nbsp&nbsp<%= undo %></span>' +
            '<span>doing:&nbsp&nbsp<%= doing %></span>' +
            '<span>succ:&nbsp&nbsp<%= succ %></span>' +
            '<span>paused:&nbsp&nbsp<%= paused %></span>' +
            '<span>error:&nbsp&nbsp<%= error %></span>' +
            '<span>fail:&nbsp&nbsp<%= fail %></span>');

    var renderDeployStatus = function (rid, data) {
        if (!data) {
            $(".job-status").text("undo");
            // $(".server-status").text("undo");
            $('.console-host').attr('data-status', 'undo');
        } else {
            var stop_status = ["succ", "fail", "error", "stopped"];
            if ($(".job-status").text() != data.status) {
                $(".job-status").text(data.status);
                if (_.contains(stop_status, data.status))
                    createNotification("任务状态改变: " + data.status, {"body": "tid: " + rid}, 5000);
                /*
                 *job status changed, so re-render the ConsoleTable
                 */
                setTimeout(function () {
                    renderConsoleTable();
                }, 1000);
            }

            var status_count = {};
            STATUS_SEQUENCE.forEach(function(i) {
                status_count[i] = 0;
            });

            $('.console-host').each(function() {
                var $host = $(this),
                    hostname = $host.attr('data-server'),
                    status = data.detail[hostname];
                $host.attr('data-status', status);
                status_count[status] += 1;
            });

            // Show status count
            console.log('status count', status_count);
            $('.job-status-count').html(
                status_count_template(status_count));

            tinysort('.job-servers>.console-host', {
                sortFunction: function(a, b) {
                    var a_status = $(a.elm).attr('data-status'),
                        b_status = $(b.elm).attr('data-status'),
                        a_index = get_seq_index(a_status),
                        b_index = get_seq_index(b_status);
                    console.log('sort', a_status, b_status, a_index, b_index);
                    return a_index===b_index?0:(a_index>b_index?1:-1);
                }
            });
        }
    };

    var createNotification = function (title, params, autoclose) {
        var permission = notify.permissionLevel();
        if (permission === "default") {
            notify.requestPermission();
        } else if (permission === "denied") {
            return false;
        }
        if (!params.hasOwnProperty("icon")) {
            params.icon = "/static/img/favicon.ico";
        }
        notify.config({autoClose:autoclose});
        notify.createNotification(title, params);
        return true;
    };


    loki.disableNumberInputScroll();
    loki.registerAjaxError();
    loki.run();
});
