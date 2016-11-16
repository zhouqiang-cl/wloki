define([
    'jquery',
    'highcharts',
    'highchartsMore',
], function($, Highcharts) {

    /* Highcharts themes */
    var namespace = 'highcharts-themes',
        themeDefaults,
        themes = {};

    themeDefaults = {
        // Normally we don't use title
        title: {
            text: null,
            style: {
                "font-size": "2em",
                "color": "#777",
            }
        },
        chart: {
            type: 'spline',
            plotShadow: false,
            backgroundColor: 'transparent',
            animation: false,
            style: {
                fontFamily: 'Helvetica',
                fontWeight: 'normal'
            },
            zoomType: "x",
        },
        xAxis: {
            type: 'datetime',
            labels: {
                align: 'center',
            },
        },
        yAxis: {
            gridLineColor: '#eee',
            title: {
                align: 'high',
                offset: 0,
                rotation: 0,
                y: -15,
            },
        },
        legend: {
            layout: 'horizontal',
            align: 'center',
            verticalAlign: 'bottom',
            itemWidth: 180,
            symbolRadius: 3,
            itemMarginBottom: 5,
            itemStyle: {
                color: '#333',
                fontWeight: 'normal',
                fontSize: 13
            }
        },
        tooltip: {
            shared: false,
            // NOTE true will cause bugs on pie chart
            // NOTE Highstock will use crosshairs by default
            crosshairs: false,
            animation: true,
            hideDelay: 0,
            useHTML: true,
            headerFormat: '<div class="title">{point.key}</div><table>',
            pointFormat: '<tr>' +
                '<td height="18"><span style="color:{series.color}">● </span>{series.name}: </td>' +
                '<td style="text-align: left"><b>{point.y}</b></td></tr>',
            footerFormat: '</table>',

            // Disable svg background, decorate tooltip by .css
            backgroundColor: "rgba(255,255,255,0)",
            borderWidth: 0,
            shadow: false,
            positioner: function(boxWidth, boxHeight, point) {
                // console.log(point.plotX, point.plotY, boxWidth, boxHeight, this.chart.plotWidth);
                var plotWidth = this.chart.plotWidth,
                    plotX = point.plotX;
                if (plotWidth - plotX + 50 < boxWidth) {
                    return {
                        x: point.plotX - boxWidth + 50,
                        y: point.plotY + 30
                    };
                } else {
                    return {
                        x: point.plotX + 50,
                        y: point.plotY + 30
                    };
                }
            },
            /*
            backgroundColor: {
                linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
                stops: [
                    [0, '#f3f3f3'],
                    [1, '#eaeaea'],
                ]
            },
            borderWidth: 1,
            borderColor: '#999',
            style: {
                color: '#333',
                opacity: 0.8,
                padding: '12px',
                fontSize: '13px',
            }
            */
        },
        credits: false
    };

    themes.base = {
        colors: ['#55A9DC', '#E66A8E', '#886DB3', '#6CC080', '#A7DBD8',
            '#90C5A9', '#7A9A95', '#FA8B60', '#93B1C6', '#004687',
            '#75A3D1', '#3B5998', '#77BA9B', '#B6A754', '#293E6A',
        ],
        plotOptions: {
            series: {
                animation: false,
                lineWidth: 1.2,
                states: {
                    hover: {
                        lineWidth: 2.2
                    }
                },
                marker: {
                    enabled: false,
                    states: {
                        hover: {
                            fillColor: null,
                            lineColor: '#fff',
                            // lineWidth: 1.2,
                            radius: 2.5
                        }
                    }
                }
            },
            line: {
                marker: {
                    symbol: 'circle',
                },
            },
            spline: {
                marker: {
                    symbol: 'circle',
                },
            },
            area: {
                stacking: "normal",
                lineWidth: 1,
            },
            bar: {
                pointWidth: 1
            },
            pie: {
                allowPointSelect: true,
                innerSize: '40%',
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                    // style: {
                    //     color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                    // }
                    style: {
                        color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                    },
                    connectorColor: 'silver'
                }
            },
            column: {
                pointWidth: 28,
                colorByPoint: true,
                dataLabels: {
                    enabled: true,
                    // rotation: -35,
                    // x: 20,
                    // y: -30,
                    x: 5,
                    color: 'black',
                    align: 'right',
                    format: '{y}',
                    style: {
                        fontSize: '10px',
                        fontFamily: 'Verdana, sans-serif',
                        //textShadow: '0 0 1px black'
                    }
                }
            }
        }
    };

    themes.gradient = {};
    $.extend(themes.gradient, themes.base);

    // Radialize the colors
    themes.gradient.colors = Highcharts.map(themes.gradient.colors, function (color) {
        return {
            radialGradient: { cx: 0.5, cy: 0.3, r: 0.7 },
            stops: [
                [0, color],
                [1, Highcharts.Color(color).brighten(-0.3).get('rgb')] // darken
            ]
        };
    });

    for (var name in themes) {
        var theme = themes[name];
        if (name !== '_defaults') {
            $.extend(true, theme, themeDefaults);
        }
    }

    $.fn[namespace] = Highcharts.themes = themes;

    window.setHighchartsTheme = Highcharts.setTheme = function(themeName) {
        var t = Highcharts.themes[themeName];
        // console.log('theme', t);
        if (t) {
            return Highcharts.setOptions(t);
        } else {
            return console.warn("Found no such theme.");
        }
    };
    Highcharts.setOptions({ global: { useUTC: false } });


    /* Util functions */

    var exports = {};


    var drawChart = exports.drawChart = function(container, extraOptions, useStock, theme) {
        Highcharts.setTheme(theme || 'base');


        var options = $.extend(true, {
                legend: {
                    enabled: true,
                },
                // NOTE this two options about tooltip don't take effect
                // when set in theme options, don't know why
                tooltip: {
                    shared: false,
                    crosshairs: false
                }
            }, extraOptions),
            series = options.series;

        if (!series || !series.length) {
            container.append($('<div class="xline-tl"></div><div class="xline-bl"></div>'))
                .append($('<div class="hint">No data</div>'));
            return;
        }

        // console.log('chart options', options);
        if (useStock) {
            options.rangeSelector = options.rangeSelector || {
                enabled: false
            };
            // console.log('drawChart', container, options);
            container.highcharts('StockChart', options);
        } else {
            // console.log('drawChart', container, options);
            container.highcharts(options);
        }
    };


    var prepareChart = exports.prepareChart = function(container) {

    };


    var enableLegendToggler = exports.enableLegendToggler = function() {
        var containers = $('[data-with-legend-toggler=true]');

        containers.each(function() {
            var container = $(this);
                toggleAll = $('<button>Toggle All</button>').click(function() {
                    // Disable
                    this.disabled = true;

                    var tg = $(this),
                        hc = tg.closest('.panel').find('.content').highcharts(),
                        flag = tg.data('toggle-flag') || false;  // means toggled or not

                    if (flag) {
                        // Check all
                        hc.series.forEach(function(s) {
                            s.show();
                        });
                    } else {
                        // Uncheck all
                        hc.series.forEach(function(s) {
                            s.hide();
                        });
                    }
                    tg.data('toggle-flag', !flag);

                    this.disabled = false;
                });
                togglers = $('<div></div>').addClass('togglers').append(toggleAll);

            container.append(togglers);
        });
    };


    var bigger_title = exports.bigger_title = function(text) {
        return "<span style=\"color:#aaa;opacity:0.5;font-size:1.5em;font-weight:bold;\">"+text+"</span>";
    };

    return exports;
});
