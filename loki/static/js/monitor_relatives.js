require([
    'jquery',
    'loki',
    'util/datatables',
    'util/tab-view',
], function($, loki, datatables, tabview) {
    loki.configure({
        restrict_nodes: true
    });


    var permillage_to_percent = function(v) {
        return (v * 100).toFixed(1);
    };


    loki.defineTabParamsHandler(function(params) {
    });


    /* Tab Views */

    var TemplateView = tabview.TabView.extend({
        tab_name: 'Template',
        ptree_config: {
            mode: 'disable',
            levels: [-1]
        },
        $el: $('#tab-1'),
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
            if (!loki.nodeTemplatesTable) {
                loki.nodeTemplatesTable = datatables.createDataTable(
                    $('.node-templates table'),
                    {
                        columns: [
                            {data: 'template'}
                        ],
                        tableTools: tabletools_config
                    },
                    $('.node-templates .fn-search')
                );
            }
            if (!loki.availableTemplatesTable) {
                loki.availableTemplatesTable = datatables.createDataTable(
                    $('.free-templates table'),
                    {
                        columns: [
                            {data: 'template'},
                        ],
                        tableTools: tabletools_config
                    },
                    $('.free-templates .fn-search')
                );
            }

            // Events
            $('.node-templates').on('click', 'tr,.DTTT_button', function() {
                var selected = loki.nodeTemplatesTable.rows('.selected').data();
                if (selected.length) {
                    $('.fn-remove-templates').disable(false);
                } else {
                    $('.fn-remove-templates').disable();
                }
            });

            $('.free-templates').on('click', 'tr,.DTTT_button', function() {
                var selected = loki.availableTemplatesTable.rows('.selected').data();
                if (selected.length) {
                    $('.fn-add-templates').disable(false);
                } else {
                    $('.fn-add-templates').disable();
                }
            });

            var disableButtons = function() {
                $('.fn-add-templates').disable();
                $('.fn-remove-templates').disable();
            };

            // Buttons
            $('.fn-add-templates').click(function() {
                var dt = loki.availableTemplatesTable,
                    rows = dt.rows('.selected').data(),
                    templates = [],
                    node = loki.getCurrentNode(),
                    btn = $(this);

                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    templates.push(row.template);
                }

                disableButtons();
                view.addTemplates(node, templates);
            });

            $('.fn-remove-templates').click(function() {
                var dt = loki.nodeTemplatesTable,
                    rows = dt.rows('.selected').data(),
                    node = loki.getCurrentNode(),
                    templates = [],
                    btn = $(this);

                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    templates.push(row.template);
                }

                disableButtons();
                view.removeTemplates(node, templates);
            });

            $('.fn-show-paste-modal').click(function() {
                loki.pasteModal = $('.paste-modal').modal();
            });

            $('.fn-paste-templates').click(function(){
                var textarea = $(".paste-modal > .body > textarea"),
                    _templates = textarea.val().split('\n'),
                    templates = [],
                    node = loki.getCurrentNode(),
                    i = 0;

                for(; i < _templates.length; i++) {
                    var template = _templates[i].strip();
                    if (template)
                        templates.push(template);
                }

                loki.pasteModal.modal('hide');
                textarea.val('');
                view.addTemplates(node, templates);
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
                    view.disableTab('仅允许在最下层节点管理模板');
                }
            });
            */

            if (!node.state.disabled) {
                console.log('valid node, render templates');
                view.renderNodeTemplates(params.nid);
                view.renderAvailableTemplates(params.nid);
                view.enableTab();
            } else {
                console.log('invalid node, clean UI');
                // loki.nodeTemplatesTable.clearData();
                // loki.availableTemplatesTable.clearData();
                // loki.availableTemplatesTable.nid = null;
                view.disableTab('不允许在最下层节点管理模板');
            }
        },

        renderNodeTemplates: function(grp_id) {
            var dt = loki.nodeTemplatesTable,
                query = {
                    type: 'template',
                    grp_id: grp_id
                },
                jqxhr;

            dt.displayProcessing();

            jqxhr = $.ajax({
                url: '/api/monitor/templates',
                data: query,
                type: 'GET'
            }).then(function(json) {
                dt.reloadData(json.data);
                dt.displayProcessing(false);
            });

            return jqxhr;
        },

        renderAvailableTemplates: function(grp_id) {
            var dt = loki.availableTemplatesTable,
                query = {
                    type: 'available',
                    grp_id: grp_id
                },
                jqxhr;

            dt.displayProcessing();

            jqxhr = $.ajax({
                url: '/api/monitor/templates',
                type: 'GET',
                data: query
            }).then(function(json) {
                dt.reloadData(json.data);
                dt.displayProcessing(false);
                dt.nid = grp_id;
            });

            return jqxhr;
        },

        addTemplates: function(node, templates) {
            var view = this;

            var data = {
                    templates: templates
                },
                defer = $.Deferred();

            $.ajax({
                url: '/api/monitor/relatives/' + node.id + '/templates',
                method: 'PUT',
                data: JSON.stringify(data),
                success: function() {
                  loki.notify("templates added successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            }).always(function() {
                $.absoluteWhen(
                    view.renderNodeTemplates(node.id),
                    view.renderAvailableTemplates(node.id)
                ).then(function() {
                    defer.resolve();
                });
            });

            return defer;
        },

        removeTemplates: function(node, templates) {
            var view = this;

            var data = {
                    templates: templates
                },
                defer = $.Deferred();

            $.ajax({
                url: '/api/monitor/relatives/' + node.id + '/templates',
                method: 'DELETE',
                data: JSON.stringify(data),
                success: function() {
                  loki.notify("templates removed successfully");
                },
                error: function(resp) {
                  loki.ajax_error_notify(resp);
                }
            }).always(function() {
                $.absoluteWhen(
                    view.renderNodeTemplates(node.id),
                    view.renderAvailableTemplates(node.id)
                ).then(function() {
                    defer.resolve();
                });
            });

            return defer;
        },

    });


    tabview.registerTabViews(TemplateView);


    loki.registerAjaxError();
    loki.run();
});
