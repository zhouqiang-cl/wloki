require([
    'moment',
    'loki',
    'util/chart',
    'util/datetime',
    'util/timepicker-widget',
    'loki-ext'
], function(moment, loki, chart, datetime, timepicker_widget) {

    var BANDWIDTH_DOMAINS = [
        'api.nosa.me',
        'ias.nosa.me',
        'apps.nosa.me',
        'adslist.nosa.me',
        'account.nosa.me',
        'click.nosa.me',
    ];

    loki.configure({
        sidebar: undefined
    });

    loki.ready(function() {
        timepicker_widget.init({
            days_ago: 3
        });
    });

    loki.defineParamsHandler(function(params) {
        // Timepicker widget
        timepicker_widget.update(params);

        var dates = timepicker_widget.get_dates();

        renderHome(dates.from, dates.to);
    });

    var renderHome = function(fd, td) {
        drawResourceUsageLine($("#panel-1"), fd, td);
        drawResourceUsagePie($("#panel-2"));
        drawProductAvailabilityChart($("#panel-3"), fd, td);
        drawProductResponseTimeChart($("#panel-4"), fd, td);
        drawDomainsChart(fd, td);
        drawProductsChart(fd, td);
    };

    var downsample = function(interval) {
        return ""+interval*10 + "m-avg:";
        //return (Math.round(interval/default_days_ago))?(Math.round(interval/default_days_ago)*10+"0m-avg:"):"";
    };

    var get_sum = function(list) {
        var s = 0;
        $(list).each(function(idx, n){
            s += n;
        });
        return s;
    };

    var drawResourceUsageLine = function(panel, start, end) {
        var down = downsample(datetime.get_interval(start, end));

        $.when(
            $.ajax({
                url: "/tsdb/api/query?type=http&m=zimsum:node.cpu_total{nodeid=0}"+timepicker_widget.get_tsdb_arg_str(),
                type: "GET",
                dataType: "json",
            }),
            $.ajax({
                url: "/tsdb/api/query?type=http&m=zimsum:"+ down +
                    "node.cpu_usage{nodeid=0}"+timepicker_widget.get_tsdb_arg_str(),
                type: "GET",
                dataType: "json",
            })
        ).then(function(resp0, resp1) {
            var data0 = resp0[0].data,
                data1 = resp1[0].data,
                last = data0[0].data[data1[0].data.length - 1][1],
                cpu = [];
            data1[0].name = 'cpu usage';
            data1[0].data.forEach(function(i) {
                cpu.push(parseInt(i[1]));
            });
            panel.find('.title').html("CPU 使用率 (总计 "+last
                +" 核，平均使用率 "+Math.round((get_sum(cpu)/cpu.length)*100)/100+"%)");
            chart.drawChart(panel.find('.content'), {
                legend: {
                    enabled: false,
                },
                yAxis: {
                    opposite: false,
                },
                series: data1,
            }, true);
        });
    };

    var drawResourceUsagePie = function(panel) {
        $.ajax({
            url: "/api/dashboard/resource_usage_percentage_summary",
            type: "GET",
            dataType: "json",
            success: function(json) {
                panel.find('.title').html('资源使用总览');

                chart.drawChart(panel.find('.content'), {
                    series: [{
                        type: "pie",
                        data: json.data,
                    }],
                }, undefined, 'gradient');
            },
        });
    };

    var drawProductAvailabilityChart = function(panel, start, end){
        $.ajax({
            url: "/api/dashboard/product_ids",
            type: "GET",
            dataType: "json",
            success: function(json){
                var down = downsample(datetime.get_interval(start, end)),
                    product_ids = json.data,
                    url = "/tsdb/api/query?type=product&m=zimsum:"+down
                        +"node.availability"+"{nodeid="+product_ids
                            .join("|")+"}"+timepicker_widget.get_tsdb_arg_str();
                $.ajax({
                    url: url,
                    type: "GET",
                    dataType: "json",
                    success: function(json){
                        panel.find('.title').html("产品线可用率 (%)");
                        chart.drawChart(panel.find('.content'), {
                            yAxis: {
                                opposite: false,
                                max: 100,
                                endOnTick: false,
                                maxPadding: 1,
                                min: null,
                                startOnTick: false,
                                minPadding: 0.1,
                                showLastLabel: true
                            },
                            series: json.data,
                        }, true);
                    },
                });
            },
        });
    };

    var drawProductResponseTimeChart = function(panel, start, end){
        var down = downsample(datetime.get_interval(start, end));
        $.ajax({
            url: "/api/dashboard/product_ids",
            type: "GET",
            dataType: "json",
            success: function(json){
                var product_ids = json.data;
                var url = "/tsdb/api/query?type=product&m=zimsum:"
                    +down+"node.responsetime"+"{nodeid="
                    +product_ids.join("|")+"}"+timepicker_widget.get_tsdb_arg_str();
                $.ajax({
                    url: url,
                    type: "GET",
                    dataType: "json",
                    success: function(json){
                        panel.find('.title').html("产品线响应时间 (ms)");
                        chart.drawChart(panel.find('.content'), {
                            marker: {
                                enabled: false,
                            },
                            yAxis: {
                                opposite: false,
                                min: 0,
                            },
                            series: json.data,
                        }, true);
                    },
                });
            },
        });
    };


    var drawDomainsChart = function(start, end) {
        $.ajax({
            url: "/api/nodes/domains?for_draw=1",
            type: "GET",
            dataType: "json",
            success: function(json) {
                var urls = json.data,
                    domains = [],
                    down = downsample(datetime.get_interval(start, end));
                for(var k in urls) {
                    var v = urls[k];
                    for(var i=0; i<v.length; i++) {
                        url = v[i];
                        if( ! domains.contains(url.domain) ) {
                            domains.push(url.domain);
                        }
                    }
                }
                drawDomainChart($("#panel-5"), {
                    key: "url.bandwidth",
                    name: "Domain Bandwidth (Bits)",
                    type: "area",
                    func: "*8",
                }, BANDWIDTH_DOMAINS, start, end);
                drawDomainChart($("#panel-6"), {
                    key: "domain.availability",
                    name: "Domain Availability(%)",
                    max: 100,
                    min: null,
                }, domains, start, end);
            },
        });
    };

    var drawDomainChart = function(panel, config, domains, start, end) {
        var down = downsample(datetime.get_interval(start, end)),
            url = "/tsdb/api/query?type=http&m=zimsum:"+down+config.key
                +"{domain="+domains.join("|")+"}"+timepicker_widget.get_tsdb_arg_str();
        $.ajax({
            url: url,
            type: "GET",
            dataType: "json",
            success: function(json) {
                if(config.func){
                    for(var i=0;i<json.data.length;i++){
                        var series = json.data[i];
                        for(var j=0;j<series.data.length;j++){
                            series.data[j][1] = eval(""+series.data[j][1]+config.func);
                        }
                    }
                }

                panel.find('.title').html(config.name);
                var draw_config = {
                    chart: {
                        type: config.type || "spline",
                        height: 500,
                    },
                    yAxis: {
                        opposite: false,
                        // Max
                        max: config.max || null,
                        endOnTick: false,
                        // Min
                        min: config.min || null,
                        minPadding: 0.01,
                        startOnTick: false,
                        showLastLabel: true
                    },
                    series: json.data,
                };
                // 对数轴
                // if (config.logarithmic) {
                //     draw_config.yAxis.type = 'logarithmic';
                //     draw_config.yAxis.minorTickInterval = 'auto';
                // }

                chart.drawChart(panel.find('.content'), draw_config, true);
            },
        });
    };



    var COLUMN_CHART_CONFIG = {
        chart: {
            type: "column",
            zoomType: "y",
        },
        legend: {
            enabled: false,
        },
        tooltip: {
            enabled: false,
        },
        xAxis: {
            type: 'category',
            labels: {
                // rotation: -35,
                style: {
                    fontSize: '14px',
                    fontFamily: 'Verdana, sans-serif',
                    fontWeight: 'normal',
                    color: '#555'
                }
            }
        },
        yAxis: {
            opposite: false,
            min: 90,
        }
    };


    var drawProductsChart = function(start, end) {
        var i = datetime.get_interval(start, end);
        $.ajax({
            url: "/api/dashboard/product_summary?interval="+i+timepicker_widget.get_tsdb_arg_str(),
            type: "GET",
            dataType: "json",
            success: function(json) {
                // for(type in json.data) {
                //     var series = json.data[type];
                //     series.pointWidth = 28;
                //     series.;
                // }
                var config;

                $("#panel-7 > .title").html(i + " 天平均可用率 (%)");

                config = $.extend(true, {},
                    COLUMN_CHART_CONFIG,
                    {
                        plotOptions: {
                            column: {
                                dataLabels: {
                                    y: -30
                                }
                            }
                        },
                        series: [json.data.availability],
                        yAxis: {
                            title: {text: null},
                            max: 100,
                            min: 99,
                        },
                        chart: {
                            marginTop: 35
                        }
                    });

                chart.drawChart($("#panel-7 > .content"), config);

                $('#panel-8 > .title').html(i + " 天平均响应时间 (ms)");
                chart.drawChart(
                    $("#panel-8 > .content"),
                    $.extend({},
                        COLUMN_CHART_CONFIG,
                        {
                            series: [json.data.response_time],
                            yAxis: {
                                min: 0,
                            },
                        })
                );
            },
        });
    };

    loki.run();
});
