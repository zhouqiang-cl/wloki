require([
    'moment',
    'loki',
    'util/chart',
    'util/datetime',
    'util/timepicker-widget',
    'loki-ext'
], function (moment, loki, chart, datetime, timepicker_widget) {

    var interval_unit = 3;

    loki.configure({
        sidebar: 'domains'
    });

    loki.ready(function() {
        timepicker_widget.init();

        $("#sidebar .content").on("click", "a", function(e){
            e.preventDefault();
            var params = loki.getParams();
                domain = $(this).text();
            params.domain = domain;
            loki.route('?' + $.param(params));
        });
    });

    loki.defineParamsHandler(function(params) {
        // Timepicker widget
        timepicker_widget.update(params);

        if(!params.domain) {
            initSummary();
        } else {
            renderDomain(params.domain);
        }
    });

    function drawDomainChart(panel, configs, domain) {
        var down = downsample();
        $(configs).each(function(idx, config){
            (function(panel, config, domain){
                var graph = $("<div class=\"pure-u-1 panel\"></div>"),
                    url = "/tsdb/api/query?type=domain"+timepicker_widget.get_tsdb_arg_str()
                    +"&m=zimsum:"+down+config.key+"{domain="+domain+",path=*}";
                panel.append(graph);
                $.ajax({
                    url: url,
                    type: "GET",
                    dataType: "json",
                    success: function(json) {
                        var series = json.data,
                            panel_title = $("<div class=\"title\">"+config.name+" &#187; <span class=\"opacity6\">"+domain+"</span></div>"),
                            panel_content = $("<div class=\"content\"></div>");
                        graph.append(panel_title);
                        graph.append(panel_content);
                        chart.drawChart(panel_content, {
                            chart: {
                                events: {
                                    load: function(event) {
                                        this.series.forEach(function(d,i) {
                                            if(d.options.data.length<200)
                                                d.hide();
                                        });
                                    }
                                },
                            },
                            yAxis: {
                                title: {
                                    text: '',
                                },
                                min: config.min==undefined?null:0,
                            },
                            series: series,
                        });
                    },
                });
            })(panel, config, domain);
        });
    }

    var initSummary = function() {
        var dtds = [];
        dtds.push(
            $.ajax({
                url: "/api/draw/domain_configs",
                type: "GET",
                dataType: "json"
            })
        );
        dtds.push(
            $.ajax({
                url: "/api/nodes/domains?for_draw=1",
                type: "GET",
                dataType: "json",
            })
        );

        // when both ajax are done
        $.when.apply($, dtds).done(function(){
            var domain_configs = arguments[0],
                urls = arguments[1],
                domains = [];
            if (domain_configs[1] != "success")
                humane.error("get domain_configs error");
            if (urls[1] != "success")
                humane.error("get domains error");
            domain_configs = domain_configs[0].data;
            urls = urls[0].data;
            for( var k in urls) {
                var v = urls[k];
                for(var i=0; i<v.length; i++) {
                    url = v[i];
                    if( ! domains.contains(url.domain) ) {
                        domains.push(url.domain);
                    }
                }
            }

            var container = $("#panel-domain-container");
            container.empty();
            for(var i=0; i<domain_configs.length; i++) {
                var panel = $("<div class=\"pure-u-1 panel\"></div>").attr('data-with-legend-toggler', 'true'),
                    config = domain_configs[i];
                container.append(panel);
                drawDomainSummary(panel, config, domains);
            }

            chart.enableLegendToggler();
        });
    };


    var drawDomainSummary = function(panel, config, domains) {
        var down = downsample(),
            url = "/tsdb/api/query?type=http&m=zimsum:20m-avg:"+config.key+"{domain="
                +domains.join("|")+"}"+timepicker_widget.get_tsdb_arg_str(),
            panel_title = $("<div class=\"title\">"+config.name+"</div>"),
            panel_content = $("<div class=\"content\"></div>");
            panel.append(panel_title);
            panel.append(panel_content);
        $.ajax({
            url: url,
            type: "GET",
            dataType: "json",
            success: function(json) {
                chart.drawChart(panel_content, {
                    yAxis: {
                        min: config.min,
                    },
                    series: json.data
                });
            },
        });
    };

    var renderDomain = function(domain){
        $.ajax({
            url: "/api/draw/http_configs",
            type: "GET",
            dataType: "json",
            success: function(json){
                var panel = $("#panel-domain-container");
                panel.empty();
                drawDomainChart(panel, json.data, domain);
            },
        });
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
