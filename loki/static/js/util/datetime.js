define([
    'moment'
], function(moment) {
    var exports = {};

    DEFAULT_FORMAT = 'YYYY/MM/DD';

    var parse_unix_offset  = function(offset, format) {
            if (format === undefined)
                format = DEFAULT_FORMAT;
            return moment(offset).format('YYYY/MM/DD');
        },

        milliseconds_ago = exports.milliseconds_ago = function(milliseconds, format) {
            if (format === undefined)
                format = DEFAULT_FORMAT;
            return moment(Date.parse(new Date()) - milliseconds).format(format);
        },

        seconds_ago = exports.seconds_ago = function(seconds, format) {
            return milliseconds_ago(seconds * 1000, format);
        },

        minutes_ago = exports.minutes_ago = function(minutes, format) {
            return seconds_ago(minutes * 60, format);
        },

        hours_ago = exports.hours_ago = function(hours, format) {
            return minutes_ago(hours * 60, format);
        },

        days_ago = exports.days_ago = function(days, format) {
            return hours_ago(days * 24, format);
        };


    var getDateStr = exports.getDateStr = function(days, from_date, to_date) {
        var date_str = "",
            rv;
        if(from_date) {
            date_str += "&start="+from_date.replace(/\-/g, "/");
            if(to_date && (moment(new Date()).format("YYYY-MM-DD")!=to_date)){
                date_str += "&end="+to_date.replace(/\-/g, "/");
            }
        }
        rv = date_str || "&start="+days_ago(days);
        // console.log('getDateStr', rv);
        return rv;
    };


    var get_interval = exports.get_interval = function(start, end) {
        return Math.round((moment(end)-moment(start))/(24*60*60*1000));
    };


    return exports;
});
