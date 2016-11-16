require([
    'jquery',
    'loki',
    'util/datatables'
], function($, loki, datatables) {
    loki.configure({
        tabs: {
            '1': 'User',
            '2': 'Admin',
        },
        ptree_tab_configs: {
            User: {
                mode: 'disable',
                levels: []
            },
            Admin: {
                mode: 'disable',
                levels: []
            },
        },
        // restrict_nodes: false
    });


    loki.defineTabInitializers({

        initUser: function() {

        },

        initAdmin: function() {

        },

    });


    loki.defineTabHandlers({

        handleUser: function() {

        },

        handleAdmin: function() {

        },
    });


    loki.registerAjaxError();
    loki.run();
});
