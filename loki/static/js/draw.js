require([
    'underscore',
    'highcharts',
    'jquery',
    'loki',
    'util/chart',
    'util/datetime',
    'util/timepicker-widget',
    'util/datatables',
    'selectize',
    'jquery-peity',
    'loki-ext',
], function(_, Highcharts, $, loki, chart, datetime, timepicker_widget, datatables) {
    var interval_unit = 5,
        default_days = 1,
        chartconfigs;

    Highcharts.themes.base.legend.itemWidth = null;

    loki.configure({
        tabs: {
            '1': 'Monitor',
            '2': 'HTTP',
            '3': 'Capacity',
            '4': 'Availability'
        },
        ptree_tab_configs: {
            Monitor: {
                mode: 'disable',
                levels: [0]
            },
            HTTP: {
                mode: 'enable',
                levels: [1]
            },
            Capacity: {
                mode: 'disable',
                levels: [0]
            },
            Availability: {
                mode: 'disable',
                levels: [0, 2, 3]
            },
        }
    });

    loki.ready(function() {
        timepicker_widget.init();
    });


    loki.defineParamsHandler(function(params) {
        // Timepicker widget
        timepicker_widget.update(params);
        console.log('test get_tsdb_arg_str', timepicker_widget.get_tsdb_arg_str());

        // Scroll to top
        if (params.nid)
            $('body').animate({scrollTop: 0}, 300);
    });


    loki.defineTabInitializers({
        initMonitor: function(params) {
            // Servers table
            loki.serversTable = datatables.createDataTable(
                $('.servers > table'),
                {

                    order: [[1, 'asc']],
                    columnDefs: [
                        {
                            targets: 0,
                            orderable: false
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
                        {
                            data: 'hostname',
                            render: function(data, type, row, meta) {
                                return '<span class="placeholder"></span>';
                            }
                        },
                        {
                            data: 'hostname',
                            render: function(data, type, row, meta) {
                                return '<span class="placeholder"></span>';
                            }
                        },
                        {
                            data: 'hostname',
                            render: function(data, type, row, meta) {
                                return '<span class="placeholder"></span>';
                            }
                        },
                    ],
                    scrollY: '300px',
                    // dom: '<"clear">lrti',
                }
            );

            // Select all checkbox
            $('.servers').on('click', '.select-all', function(e) {
                var toggler = $(e.currentTarget),
                    table = $('.servers table').eq(1),
                    flag = toggler.data('selectall') || false;
                table.find('tbody td input[type="checkbox"]').prop('checked', !flag);
                toggler.data('selectall', !flag);

                if (getSelectedServers().length > 0) {
                    $('.fn-draw').prop('disabled', false);
                } else {
                    $('.fn-draw').prop('disabled', true);
                }
            });

            $('.servers').on('change', 'tbody input[type="checkbox"]', function() {
                if (getSelectedServers().length > 0) {
                    $('.fn-draw').prop('disabled', false);
                } else {
                    $('.fn-draw').prop('disabled', true);
                }

                $('.servers .select-all').prop('checked', false).data('selectall', false);
            });

            // Peity button
            $('.fn-peity').click(function() {
                var button = $(this);
                button.prop('disabled', true);

                $.absoluteWhen.apply($,
                    processPeity()
                ).then(function() {
                    button.prop('disabled', false);
                });
            });

            // Draw button
            $('.fn-draw').click(function() {
                var button = $(this);
                button.prop('disabled', true);

                $.absoluteWhen.apply($,
                    drawSystemCharts()
                ).then(function() {
                    button.prop('disabled', false);
                });
            });
        },

        initHTTP: function(params) {
        },

        initCapacity: function(params) {
        },

        initAvailability: function(params) {
        },
    });


    /* Functionals */
    loki.defineTabHandlers({
        handleMonitor: function(params) {
            // Datatypes
            fetchDatatypes(_.partial(renderDatatypes, params.dt));

            $("#panel-system-container").empty();

            // Servers
            if (params.nid) {
                fetchServers(params.nid, renderServers);
            } else {
                //renderNoServers();
            }
        },

        handleHTTP: function(params) {
            var nid = params.nid;
            if(!nid) return;
            $("#panel-http-container").empty();
            if ( ! nid )
                return;

            var dtds = [];
            dtds.push(
                $.ajax({
                    url: "/api/draw/http_configs",
                    type: "GET",
                    dataType: "json"
                })
            );
            dtds.push(
                $.ajax({
                    url: '/api/nodes/' + nid + '/domains',
                    type: "GET",
                    dataType: "json",
                })
            );

            // when both ajax are done
            $.when.apply($, dtds).done(function(){
                var http_configs = arguments[0],
                    urls_configs = arguments[1];
                if (http_configs[1] != "success")
                    loki.notify("get http_configs error", 'error');
                if (urls_configs[1] != "success")
                    loki.notify("get domains error", 'error');
                http_configs = http_configs[0].data;
                var urls = urls_configs[0].data;
                if(!urls.length) {
                    return;
                }
                for(var i=0; i<http_configs.length; i++) {
                    var config = http_configs[i],
                        panel = loki.createPanel({
                            class_: 'pure-u-1',
                            attr: {'data-with-legend-toggler': 'true'},
                            parent: $("#panel-http-container"),
                            inner: [$('<div class="title">' + config.name + '</div>'),
                                    $('<div class="content"></div>')]
                        });
                    drawHTTPChart(panel, config, urls);
                }
                chart.enableLegendToggler();
            });
        },

        handleCapacity: function(params) {
            var nid = params.nid;
            if(!nid) return;
            $("#panel-usage-container").empty();
            $.ajax({
                url: "/api/draw/usage_configs",
                type: "GET",
                dataType: "json",
                success: function(json) {
                    for(var i=0; i<json.data.length; i++) {
                        var config = json.data[i],
                            panel = loki.createPanel({
                                class_: 'pure-u-1',
                                parent: $("#panel-usage-container"),
                                inner: [$('<div class="title"></div>'),
                                        $('<div class="content"></div>')]
                            });
                        drawUsageChart(panel, config, nid);
                    }
                },
            });
        },

        handleAvailability: function(params) {
            var nid = params.nid;
            if(!nid) return;
            $("#panel-availability-container").empty();
            $.ajax({
                url: "/api/draw/availability_configs",
                type: "GET",
                dataType: "json",
                success: function(json) {
                    for(var i=0; i<json.data.length; i++) {
                        var config = json.data[i],
                            panel = loki.createPanel({
                                class_: 'pure-u-1',
                                parent: $("#panel-availability-container"),
                                inner: [$('<div class="title">' + config.name + '</div>'),
                                        $('<div class="content"></div>')]
                            });
                        drawAvailabilityChart(panel, config, nid);
                    }
                },
            })
        },
    });


    var fetchServers = function(nid, cb) {
        $.ajax({
            url: '/api/servers?type=recursive&node_id=' + nid,
            success: function(json) {
                cb(json.data);
            }
        });
    };


    var renderServers = function(servers) {
        var dt = loki.serversTable;
        dt.reloadData(servers);

        if (servers.length > 0) {
            $('.fn-peity').prop('disabled', false);
        } else {
            $('.fn-peity').prop('disabled', true);
        }

        $('.fn-draw').prop('disabled', true);
    };


    var getSelectedServers = function() {
        var selectedServers = [];
        $('.servers table tbody td input[type="checkbox"]:checked').each(function() {
            selectedServers.push($(this).val());
        });
        return selectedServers;
    };


    var processPeity = function() {
        var ajaxQueue = [],
            peityColumns = [];
        $('.servers table').eq(0).find('> thead > tr > th').each(function(i, td) {
            var metric = $(td).attr('data-metric');
            if (metric)
                peityColumns.push({index: i, metric: metric});
        });

        $('.servers table').eq(1).find('> tbody > tr').each(function() {
            var tr = $(this),
                tds = tr.find('> td');
            for (var i = 0; i < peityColumns.length; i++) {
                var c = peityColumns[i],
                    host = tds.eq(1).text(),
                    td = tds.eq(c.index);

                tdStartSpinner(td);

                ajaxQueue.push(
                    fetchMetric.call(td, host, c.metric, renderMetric)
                );
            }
        });


        return ajaxQueue;
    };


    var fetchMetric = function(host, metric, renderer) {
        var td = this;
        return $.ajax({
            url: "/tsdb/api/query?start=" + datetime.minutes_ago(30) +
                "&m=zimsum:"+metric+"{endpoint="+host+"}&type=peity",
            type: "GET",
            dataType: "json",
            success: function(data) {
                if (data.data.length) {
                    renderer(td, data.data);
                } else {
                    tdEndSpinner(td);
                    td.find("span").remove();
                    td.append($("<span class=\"error\">No data</span>"));
                }
            },
            error: function() {
                tdEndSpinner(td);
                td.find("span").remove();
                td.append($("<span class=\"error\">Could not fetch data</span>"));
            }
        });
    };

    var renderMetric = function(td, data) {
        tdEndSpinner(td);

        var span = $('<span></span>').text(data.join(','));
        td.empty().append(span);
        span.peity('line', {
            height: 20,
            width: '70%'
        });
    };


    var tdStartSpinner = function(td) {
        var spinner = $('<div class="spinner">' +
            '<div class="bounce1"></div>' +
            '<div class="bounce2"></div>' +
            '<div class="bounce3"></div>' +
            '</div>');
        td.empty().append(spinner);
    };


    var tdEndSpinner = function(td) {
        td.find('.spinner').remove();
    };


    var drawSystemCharts = function() {
        var ajaxQueue = [];

        $("#panel-system-container").empty();

        var selectedServers = getSelectedServers();
        var metric_type = $("#input-datatype").selectize().val();
        if(! metric_type) {
            loki.notify("select monitor type", 'error');
            return;
        }
        if(! selectedServers.length) {
            loki.notify("select servers", 'error');
            return;
        }
        if(selectedServers.length>10) {
            loki.notify("too many servers selected, should be less than 10", 'error');
            return;
        }

        var metrics = [];
        $(chartconfigs[0].items).each(function(index, metric){
            if(metric.type == metric_type) {
                $(metric.items).each(function(idx, m){
                    metrics.push(m);
                });
            }
        });
        $(metrics).each(function(idx, m){
            var down = downsample(),
                url = "/tsdb/api/query?type=system&m=zimsum:"+down+m.key+"{",
                tagStr = "endpoint="+selectedServers.join("|");

            if(m.config && m.config.tags && m.config.tags.length > 0) {
                tagStr += ",";
                $(m.config.tags).each(function(idx, tag){
                    tagStr += tag+"=*";
                });
            }
            url += tagStr;
            url += "}";
            url += timepicker_widget.get_tsdb_arg_str(default_days);

            var panel = loki.createPanel({
                class_: 'panel chart-panel',
                parent: $("#panel-system-container"),
                inner: [$('<div class="title">'+m.key+'</div>'), $('<div class="content"></div>')]
            });

            var jqxhr = $.ajax({
                url: url,
                type: "GET",
                dataType: "json",
                success: function(json){
                    chart.drawChart(panel.find('.content'), {
                        series: json.data
                    });
                },
            });
            ajaxQueue.push(jqxhr);
        });
        return ajaxQueue;
    };

    var drawHTTPChart = function(panel, config, urls) {
        var dtds = [],
            down = downsample();

        for(var i=0; i<urls.length; i++) {
            var url = urls[i];
            dtds.push($.ajax({
                url: "/tsdb/api/query?m=zimsum:"+down+config.key
                    +"{domain="+url.domain+",path="+url.path
                    +"}&type=http"+timepicker_widget.get_tsdb_arg_str(default_days),
                type: "GET",
                dataType: "json"
            }));
        }

        $.absoluteWhen.apply($, dtds).then(function(){
            var series = [];
            if(arguments.length == 3 && typeof(arguments[1]) == 'string'){
                arguments = [arguments, ];
            }
            for(var i=0; i<arguments.length; i++){
                if(arguments[i][1] == 'error' || arguments[i][0].data.length === 0)
                    continue;
                series.push(arguments[i][0].data[0]);
            }
            chart.drawChart(panel.find('.content'), {
                yAxis: {
                    min: config.min==undefined?null:0,
                },
                series: series,
            });
        });
    };

    var drawUsageChart = function(panel, config, nid) {
        var down = downsample();
        $.ajax({
            url: "/tsdb/api/query?m=zimsum:"+down
                +config.key+"{nodeid="+nid+"}"
                +timepicker_widget.get_tsdb_arg_str(default_days),
            type: "GET",
            dataType: "json",
            success: function(json) {
                fillUsageDesc(panel.find('.title'), config);

                chart.drawChart(panel.find('.content'), {
                    legend: {
                        enabled: false,
                    },
                    series: json.data,
                });
            }
        });
    };


    var drawAvailabilityChart = function(panel, config, nid) {
        var down = downsample();

        $.ajax({
            url: "/tsdb/api/query?m=zimsum:"+down+config.key
                +"{nodeid="+nid+"}&type=http"+timepicker_widget.get_tsdb_arg_str(default_days),
            type: "GET",
            dataType: "json",
            success: function(json){
                chart.drawChart(panel.find('.content'), {
                    legend: {
                        enabled: false,
                    },
                    yAxis: {
                        min: config.min==undefined?null:0,
                    },
                    series: json.data,
                });
            },
        });
    };


    var fillUsageDesc = function(title, config) {
        var str = config.key;
        if(config.default_info) {
            title.html(str+" (总计"+config.default_info+")");
            return;
        }
        if(!config.key_of_total)
            return;
        var params = loki.getParams();
            url = "/tsdb/api/query?m=zimsum:"+config.key_of_total
                +"{nodeid="+params.nid+"}"+"&start="+datetime.days_ago(1);
        $.ajax({
            url: url,
            type: "GET",
            dataType: "json",
            success: function(json) {
                if (!json.data.length) {
                    title.html(
                        str + ' <small style="color:red">无总计数据!</small>'
                    );
                } else {
                    var item = json.data[0].data;
                    title.html(
                        str + ' (总计' + item[item.length - 1][1] +
                        ' ' + config.key_of_total_unit + ')'
                    );
                }
            }
        });
    };

    var fetchDatatypes = function(cb) {
        $.ajax({
            url: '/api/draw/configs',
            success: function(json) {
                cb(json.data);
            }
        });
    };

    var renderDatatypes = function(selected, configs) {
        var optgroups = [],
            options = [];
        chartconfigs = configs;

        for (var k in configs) {
            var cat = configs[k],
                og = {
                value: cat.category,
                label: cat.name,
            };
            optgroups.push(og);

            for (var kk in cat.items) {
                var typ = cat.items[kk],
                    o = {
                    category: cat.category,
                    value: typ.type,
                    name: typ.type
                };
                options.push(o);
            }
        }


        var $select = $('#input-datatype').selectize({
            options: options,
            optgroups: optgroups,
            optgroupField: 'category',
            labelField: 'name',
            searchField: ['name'],
            render: {
                optgroup_header: function(data, escape) {
                    return '<div class="optgroup-header">'
                        + escape(data.value) + ' <span class="scientific">'
                        + escape(data.label) + '</span></div>';
                }
            }
        });
        var selectize = $select[0].selectize;
        selectize.setValue(Object.keys(selectize.options)[0]);
    };


    var downsample = function() {
        var params = loki.getParams(),
            start = params.fd || datetime.days_ago(1),
            end = params.td || datetime.days_ago(0),
            i = datetime.get_interval(start, end),
            minutes = interval_unit;
        if(i>1) {
            minutes *= i;
        }
        return ""+minutes+"m-avg:";
    };



    loki.registerAjaxError();
    loki.run();
});
