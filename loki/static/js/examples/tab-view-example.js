require([
    'jquery',
    'loki',
    'util/datatables',
    'util/tab-view',
], function($, loki, datatables, tabview) {

    var OneTabView = tabview.TabView.extend({
        tab_name: 'One',
        ptree_config: {
            // levels_disabled: [0, 1, 3]
            // mode: 'disable',
            // levels: [0, 1]
            mode: 'disable',
            levels: [-1]
        },

        $el: $('#tab-1'),

        events: {
            'click .something': 'onClickSomething',
        },

        table_options: {
            columns: [
                {data: 'name'},
                {data: 'type'},
                {data: 'is_in_use'}
            ],
            rowCallback: function(row, data) {
                if (data.node_id != loki.getCurrentNode().id) {
                    $(row).addClass('row-parent');
                }
            },
        },
        $table: $('#some-table'),
        $table_search: $('.somewhere .fn-search'),

        initialize: function() {
        },

        /* Event handlers */
        onClickSomething: function() {
            // loki.route_params({rid: null});
        },
    });


    var TwoTabView = tabview.TabView.extend({
        tab_name: 'Two',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-2'),
        events: {
            'click .item': 'onClickItem',
        },

        initialize: function() {
        },
    });

    tabview.registerTabViews(OneTabView, TwoTabView);

    loki.registerAjaxError();
    loki.run();
});
