define([
    'jquery',
    'loki',
    'moment',
    'util/datetime',
    'util/timepicker'
], function($, loki, moment, datetime, timepicker) {
    var exports = {};


    var options = {
            date_format: 'YYYY-MM-DD',
            days_ago: 1,
            force_refresh: false
        },
        pickers = {},
        get_elements = function() {
            var widget = $('.timepicker-widget'),
                from_input = widget.find('input[name="from_date"]'),
                to_input = widget.find('input[name="to_date"]');
            return [widget, from_input, to_input];
        };


    var get_dates = exports.get_dates = function() {
        var _els = get_elements(),
            from_input = _els[1],
            to_input = _els[2],
            dates = {
                from: from_input.val(),
                to: to_input.val()
            };
        return dates;
    };


    var get_tsdb_arg_str = exports.get_tsdb_arg_str = function() {
        var params = loki.getParams(),
            from_date = params.fd,
            to_date = params.td,
            arg_str = '';

        if (from_date) {
            arg_str += '&start=' + from_date.replace(/\-/g, "/");
            if (to_date && (moment(new Date()).format(options.date_format) != to_date)) {
                arg_str += '&end=' + to_date.replace(/\-/g, "/");
            }
        }

        arg_str = arg_str || '&start=' + datetime.days_ago(options.days_ago);
        return arg_str;
    };


    var init = exports.init =  function(_options) {
        // console.log('timepicker widget init');

        if (_options === undefined) _options = {};
        $.extend(options, _options);

        var _els = get_elements(),
            widget = _els[0],
            from_input = _els[1],
            to_input = _els[2],
            get_from_date = function() {
                return from_input.val();
            },
            get_to_date = function() {
                return to_input.val();
            };

        // Init pikaday
        pickers.from = timepicker.render(from_input);
        pickers.to = timepicker.render(to_input);

        // Bind events
        widget
            .on('click', '.fn-apply-time', function() {
                var params = loki.getParams();
                params.fd = get_from_date();
                params.td = get_to_date();

                _route_params(params);
            })
            .on('click', '.fn-zoom-in', function() {
                var params = loki.getParams(),
                    current_from_date = get_from_date(),
                    current_to_date = get_to_date();
                if(moment(current_to_date)-moment(current_from_date)==(24*60*60*1000))
                    return;
                params.fd = moment(moment(current_from_date)+24*60*60*1000).format("YYYY-MM-DD");
                params.td = current_to_date;

                _route_params(params);
            })
            .on('click', '.fn-zoom-out', function() {
                var params = loki.getParams();
                params.fd = moment(moment(get_from_date())-24*60*60*1000).format("YYYY-MM-DD");
                params.td = $('.datepicker[name="to_date"]').val();

                _route_params(params);
            });
    };


    var _route_params = function(params) {
        if (options.force_refresh) {
            window.location.href = window.location.pathname + '?' + $.param(params);
        } else{
            loki.route('?' + $.param(params));
        }
    };


    var update = exports.update = function(params) {
        // console.log('timepicker widget update');

        var from_date = params.fd || datetime.days_ago(options.days_ago, options.date_format),
            to_date = params.td || datetime.days_ago(0, options.date_format);

        pickers.from.setDate(from_date);
        pickers.to.setDate(to_date);
    };


    return exports;
});
