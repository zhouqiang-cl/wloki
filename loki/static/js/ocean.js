require([
    'jquery',
    'loki',
    'go',
    'util/datatables',
    'util/tab-view',
    'selectize',
], function($, loki, go, datatables, tabview) {
    loki.configure({
        tabs: {
            '1': 'ReplSpider',
            '2': 'CustomDraw',
        },
        tab_views: {},
        ptree_tab_configs: {
            ReplSpider: {
                mode: 'enable',
                levels: []
            },
            CustomDraw: {
                mode: 'disable',
                levels: [0]
            },
        }
    });


    var CustomDrawTabView = tabview.TabView.extend({
        $el: $('#tab-2'),

        table_options: {
            order: [[1, 'asc']],
            columnDefs: [
                {
                    targets: 0,
                    orderable: false,
                }
            ],
            columns: [
                {
                    data: 'hostname',
                    className: 'disable-select',
                    render: function(data, type, row, meta) {
                        s = '<label for="select-' + data + '" class="pure-checkbox">' +
                            '<input id="select-' + data + '" class="select-item" type="checkbox" value="' + data + '">' +
                            '</label>';
                        return s;
                    }
                },
                {
                    data: 'hostname'
                },
            ]
        },

        $table: $('#server-table'),
        $table_search: $('.servers .fn-search'),
        table_selectable: false,

        fetchTableData: function(nid) {
            var aj = $.ajax({
                url: '/api/servers?type=recursive&node_id=' + nid,
                dataType: 'json'
            });
            return aj;
        },

        initialize: function() {
            var _this = this,
                wrapper = this.$table.closest('.dataTables_scroll'),
                metrics_input = this.$el.find('.input-metrics');

            // Table select all checkbox
            wrapper
                .on('click', '.select-all', function(e) {
                    console.log('select all');
                    var toggler = $(e.currentTarget),
                        flag = toggler.data('selectall') || false;
                    _this.$table.find('tbody td input[type="checkbox"]').prop('checked', !flag);
                    toggler.data('selectall', !flag);

                    /*
                    if (getSelectedServers().length > 0) {
                        $('.fn-draw').prop('disabled', false);
                    } else {
                        $('.fn-draw').prop('disabled', true);
                    }
                    */
                })
                .on('change', 'tbody input[type="checkbox"]', function() {
                    /*
                    if (getSelectedServers().length > 0) {
                        $('.fn-draw').prop('disabled', false);
                    } else {
                        $('.fn-draw').prop('disabled', true);
                    }
                    */

                    wrapper.find('.select-all').prop('checked', false).data('selectall', false);
                });

            // Metrics input
            metrics_input.selectize({
                valueField: 'name',
                labelField: 'name',
                searchField: 'name',
                create: false,
                load: function(query, callback) {
                    if (!query.length) return callback();
                    $.ajax({
                        url: 'http://loki.nosa.me/tsdbproxy/api/suggest?type=metrics&q=' + query,
                        success: function(json) {
                            var data = json.map(function (i) {
                                return {'name': i}
                            })
                            console.log(data);
                            callback(data);
                        },
                        error: _this.notifyError
                    })
                },
                onChange: function(value) {
                    _this.checkDrawArgument();
                }
            });
        }
    });


    loki.defineTabInitializers({
        initReplSpider: function() {
            var repl_content = $('.repl-spider .content');
            $('.repl-spider .fn-search').on('change', function() {
                var db = this.value;

                $.when(
                    $.ajax({
                        url: '/ocean/api/spider?database=' + db
                    })
                ).then(function(json) {
                    drawDiagram(repl_content, json.data.nodes, json.data.links);
                });
            });
        },

        initCustomDraw: function() {
            loki.tab_views.custom_draw = new CustomDrawTabView();
        }
    });


    loki.defineTabHandlers({
        handleCustomDraw: function(params) {
            loki.tab_views.custom_draw.renderTab(params);
        },
    });


    function drawDiagram(el, nodes, links) {
        var $go = go.GraphObject.make; // for conciseness in defining templates

        el.find('.diagram').remove();
        var container = $('<div></div>').addClass('diagram').appendTo(el);

        replDiagram = $go(go.Diagram, container[0], // create a Diagram for the DIV HTML element
            {
                initialContentAlignment: go.Spot.Center, // center the content
                "undoManager.isEnabled": true, // enable undo & redo
                layout: $go(go.LayeredDigraphLayout, {
                    direction: 0,
                    setsPortSpots: false
                }),
                //layout: $go(go.TreeLayout, { comparer: go.LayoutVertex.smartComparer, alignment: go.TreeLayout.AlignmentBusBranching})
            });

        // define a simple Node template
        replDiagram.nodeTemplate =
            $go(go.Node, "Auto", // the Shape will go around the TextBlock
                $go(go.Shape, "RoundedRectangle",
                    // Shape.fill is bound to Node.data.color
                    new go.Binding("fill", "color")),
                $go(go.TextBlock, {
                        margin: 3,
                        editable: true
                    }, // some room around the text
                    // TextBlock.text is bound to Node.data.key
                    new go.Binding("text", "key"))
        );

        // but use the default Link template, by not setting Diagram.linkTemplate

        // create the model data that will be represented by Nodes and Links
        replDiagram.model = new go.GraphLinksModel(nodes, links);
    }


    loki.registerAjaxError();
    loki.run();
});
