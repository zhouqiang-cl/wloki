require([
    'jquery',
    'loki',
    'util/timepicker-widget',
], function($, loki, timepicker_widget) {
    loki.configure({
        sidebar: undefined
    });

    loki.ready(function() {
        timepicker_widget.init({
            days_ago: 7,
            force_refresh: true
        });
    });


    loki.defineParamsHandler(function(params) {
        // Timepicker widget
        timepicker_widget.update(params);
        console.log('test get_tsdb_arg_str', timepicker_widget.get_tsdb_arg_str());
    });

    loki.run();
});
