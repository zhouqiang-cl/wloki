/*!
 * Global config for requirejs, shared in all modules
 */

var require = {
    baseUrl: '/static/js',
    paths: {
        humane: 'lib/humane.min',
        moment: 'lib/moment',
        highcharts: 'lib/highstock',
        highchartsMore: 'lib/highcharts-more',
        selectize: 'lib/selectize',
        underscore: 'lib/underscore-min',
        handlebars: 'lib/handlebars.min',
        datatables: 'lib/dataTables.min',
        'datatables-tabletools': 'lib/dataTables.tabletools',
        jstree: 'lib/jstree',
        go: 'lib/go',
        'desktop-notify': 'lib/desktop-notify-min',
        contents: 'lib/contents',
        sprintf: 'lib/sprintf',
        tinysort: 'lib/tinysort.min',
        mousetrap: 'lib/mousetrap.min',
        pikaday: 'lib/pikaday',

        jquery: 'lib/jquery-2.1.1',
        // jQuery plugins
        'jquery-modal': 'lib/jquery.modal',
        'jquery-history': 'lib/jquery.history',
        'jquery-datetimepicker': 'lib/jquery.datetimepicker',
        'jquery-peity': 'lib/jquery.peity.min',
        'jquery-mockjax': 'lib/jquery.mockjax.min',
    },
    shim: {
        'highchartsMore': {
            deps: ['highcharts']
        },
        'highcharts': {
            deps: ['jquery'],
            exports: 'Highcharts'
        },
        'handlebars': {
            exports: 'Handlebars'
        },
        'desktop-notify': {
            exports: 'notify'
        },
        'contents': {
            exports: 'gajus'
        },
        'jquery-modal': {
            deps: ['jquery'],
        },
        'jquery-history': {
            deps: ['jquery'],
            // Exports fetches the variable from the global context of the module
            exports: 'History'
        },
        'jquery-datetimepicker': {
            deps: ['jquery']
        },
        'jquery-peity': {
            deps: ['jquery']
        },
    },
    // urlArgs: "v=" +  (new Date()).getTime()
};
