require([
    'jquery',
    'loki',
    'util/datatables',
    'util/chart'
], function($, loki, datatables, chart) {
    $.fn.highlight = function(pat) {
        function innerHighlight(node, pat) {
            var skip = 0;
            if (node.nodeType == 3) {
                var pos = node.data.toUpperCase().indexOf(pat);
                pos -= (node.data.substr(0, pos).toUpperCase().length - node.data.substr(0, pos).length);
                if (pos >= 0) {
                    var spannode = document.createElement('span');
                    spannode.className = 'highlight';
                    var middlebit = node.splitText(pos);
                    var endbit = middlebit.splitText(pat.length);
                    var middleclone = middlebit.cloneNode(true);
                    spannode.appendChild(middleclone);
                    middlebit.parentNode.replaceChild(spannode, middlebit);
                    skip = 1;
                }
            } else if (node.nodeType == 1 && node.childNodes && !/(script|style)/i.test(node.tagName)) {
                for (var i = 0; i < node.childNodes.length; ++i) {
                    i += innerHighlight(node.childNodes[i], pat);
                }
            }
            return skip;
        }
        return this.length && pat && pat.length ? this.each(function() {
            innerHighlight(this, pat.toUpperCase());
        }) : this;
    };
    $.fn.removeHighlight = function() {
        return this.find("span.highlight").each(function() {
            this.parentNode.firstChild.nodeName;
            with(this.parentNode) {
                replaceChild(this.firstChild, this);
                normalize();
            }
        }).end();
    };

    loki.ready(function() {
        // Init main page datatable, because datatable should init only once
        initPanelMain();

        // Init sidebar, get all Codis list
        initSidebar();

        $(".codis-modal").off();
        proxyListener();
        slotListener();
        groupListener();
    });

    loki.defineParamsHandler(function(params) {
        if(!params.s && params.name) {
            renderCodis();
        }else {
            renderSummary();
        }
    });

    function readableByte(num){
        if (typeof num == 'undefined'){
            return 'NA'
        }
        var units = ["B","KB","MB","GB","PB"],
            i = 0;
        while(num/1024 > 1){
            num /= 1024;
            i += 1;
        }
        return num.toFixed(2) + " " + units[i];
    };

    function initSidebar(){
        $.ajax({
            url: '/api/redis/manage/list',
            type: "GET",
            dataType: "json"
        }).done(function(data){
            $("#sidebar .content").empty();
            var content = '';
            $.each(data, function(type, type_data){
                content += "<div class=\"title\" dis=\"1\">"+type+"<i class=\"collapse fa fa-angle-double-up\"></i></div>";
                content += "<ul class=\"items ui-itemlist\">";
                $.each(type_data, function(clu, clu_list){
                    $.each(clu_list, function(_, name){
                        content += "<li><a href=/redis?name="+clu+"-"+name+">"+clu+"-"+name+"</a></li>";
                    });
                });
                content += "</ul>";
            });
            $("#sidebar .content").append(content);
        }).fail(function(e){
            console.log('get redis list error! ' + e.responseText);
            loki.notify("get redis list error!");
        });

        $("#sidebar .content").on("click", "a", function(e){
            e.preventDefault();
            var redisName = $(this).text();
            loki.route("?name=" + redisName);
        });

        $("#sidebar .content").on("click", 'i', function(){
            var display = parseInt($(this).parent().attr("dis"));
            display = (display+1)%2;
            if(display){
                $(this).removeClass("fa-angle-double-down");
                $(this).addClass("fa-angle-double-up");
                $(this).parent().next().css("display","block");
            }else{
                $(this).removeClass("fa-angle-double-up");
                $(this).addClass("fa-angle-double-down");
                $(this).parent().next().css("display","none");
            }
            $(this).parent().attr("dis", display);
        });
    };

    function initPanelMain(){
        var container = ".container .container-main";
        $(".manage-modal").off();

        var serverTableCodis = datatables.createDataTable(
            $('.server-table-codis'), {
                columns: [
                    {data: 'name'},
                    {data: 'zk'},
                    {data: 'dashboard'},
                    {data: 'proxy'}
                ],
                scrollY: '300px',
                scrollCollapse: true,
                autoWidth: false,
            });
        loki.serverTableCodis = serverTableCodis;
        var serverTableRedis = datatables.createDataTable(
            $('.server-table-redis'), {
                columns: [
                    {data: 'host'},
                    {data: 'port'},
                    {data: 'status'},
                    {data: 'master_host'},
                    {data: 'master_port'},
                    {data: 'cluster'},
                    {data: 'used_memory'},
                    {data: 'conf_maxmemory'},
                    {data: 'conf_dir'},
                    {data: 'conf_dbfilename'}
                ],
                scrollY: '300px',
                scrollCollapse: true,
                autoWidth: false,
            });
        loki.serverTableRedis = serverTableRedis;

        $(container + " .main-search form").on('submit', function(e) {
            e.preventDefault();
            var params = loki.getParams(),
                s = $(container + " .main-search form input").val();
            loki.route_params({s: s});
        });

        // Add redis modal listener
        $(container + " .main-button").on("click", '.manage-redis', function(){
            loki.setSlotModal = $('.manage-redis-modal').modal();
            $('.manage-redis-modal .body #redis-host').focus();
        });
        $('.manage-redis-modal .manage-redis-form').on('submit', function(e){
            e.preventDefault();
            var host = $('.manage-redis-modal .body #redis-host').val(),
                port = $('.manage-redis-modal .body #redis-port').val(),
                status = $('.manage-redis-modal .body #redis-status').val();
            loki.setSlotModal.modal('hide');
            $('.manage-redis-modal .body input').val('');
            $('.manage-redis-modal .body #redis-status').val('online');
            $.ajax({
                url: "/api/redis/manage/redis",
                type: "POST",
                data: JSON.stringify({
                    host: host,
                    port: new Number(port),
                    status: status
                }),
                dataType: "text"
            }).done(function(){
                loki.notify("update redis OK", "info");
            }).fail(function(e){
                console.log('update redis error! ' + e.responseText);
                loki.notify("update redis error!", "error");
            });
        })

        // Add codis modal listener
        $(container + " .main-button").on("click", '.manage-codis', function(){
            loki.setSlotModal = $('.manage-codis-modal').modal();
            $('.manage-codis-modal .body #codis-name').focus();
        });
        $('.manage-codis-modal .manage-codis-form').on('submit', function(e){
            e.preventDefault();
            var name = $('.manage-codis-modal .body #codis-name').val(),
                zk = $('.manage-codis-modal .body #codis-zk').val();
            loki.setSlotModal.modal('hide');
            $('.manage-codis-modal .body input').val('');
            $.ajax({
                url: "/api/redis/manage/codis",
                type: "POST",
                data: JSON.stringify({
                    name: name,
                    zk: zk
                }),
                dataType: "text"
            }).done(function(){
                loki.notify("update codis OK", "info");
            }).fail(function(e){
                console.log('update codis error! ' + e.responseText);
                loki.notify("update codis error!", "error");
            });
        })
    };

    function renderSummary() {
        var panel = ".container .container-main",
            s = loki.getParams().s;

        $(panel + " form input").val(s);

        $(panel).siblings().hide();
        $(panel).show();
        
        if(s == undefined){
            $(panel + ' .search-result').hide();
            return;
        }else{
            $(panel + ' .search-result').show();
        }
        // Should place here after $(panel).show()
        loki.serverTableCodis.clearData();
        loki.serverTableRedis.clearData();

        $.ajax({
            url: "/api/redis/manage/search",
            type: "GET",
            data: {s: s},
            dataType: "json"
        }).done(function(data){
            if('codis' in data){
                data_codis = data['codis'];
                loki.serverTableCodis.reloadData(data_codis);
            }
            if('redis' in data){
                data_redis = data['redis'];
                loki.serverTableRedis.reloadData(data_redis);
            }
            // highlight keyword
            $(panel + ' .search-result').highlight(s);
        }).fail(function(e){
            console.log("search error! " + e.responseText);
            loki.notify("search error!");
        });
    };

    function renderOverview(){
        var name = loki.getParams().name,
            interval = loki.overviewInterval,
            container = loki.redis_overviewContent;
        clearTimeout(loki.renderOverviewTimer);

        $.ajax({
            url: "/api/redis/" + name + "/overview",
            type: "GET",
            timeout: interval/2,
            dataType: "json"
        }).done(function(json){
            $(container + " dd:eq(0)").text(json.product);
            $(container + " dd:eq(1)").text(json.zk);
            $(container + " dd:eq(2)").text(readableByte(json.memory));
            $(container + " dd:eq(3)").text(json.keys);
            $(container + " dd:eq(4)").text(json.ops<0?0:json.ops);
            $(container + " dd:eq(5)").text(json.dashboard);
        }).fail(function(e){
            console.log('get overview error! ' + e.responseText);
        }).always(function(){
            loki.renderOverviewTimer = setTimeout(function(){
                renderOverview();
            }, interval);
        });
    };

    function proxyListener (){
        $("#proxyView").off("click");
        $("#proxyView").on("click", ".button-refresh", function(){
            renderProxy();
        });
        $('#proxyView').on('click', '.fn-proxy-online', function(){
            var proxy_id = $(this).attr('proxy-id');
            var name = loki.getParams().name;
            if(confirm(name +" set "+proxy_id+" online ?")){
                var sendData = {'proxy_id': proxy_id, 'state': 'ON'};
                $.ajax({
                    url: "/api/redis/"+name+"/proxy",
                    type: "POST",
                    data: sendData,
                    dataType: "json"
                }).done(function(){
                    renderProxy();
                }).fail(function(e){
                    console.log('set proxy error! ' + e.responseText);
                    loki.notify("set proxy error!", "error");
                    renderProxy();
                });
            }
        });
    };

    function renderProxy() {
        var name = loki.getParams().name,
            container = loki.redis_proxyContent;
        $(container).empty();
        $.ajax({
            url: "/api/redis/" + name + "/proxy",
            type: "GET",
            dataType: "json"
        }).done(function(json){
            var content = "<table class=\"pure-table pure-table-horizontal\"><thead>"
                + "<tr><th>ProxyId</th><th>Addr</th><th>DebugAddr</th><th>State</th><th>Action</th></tr>"
                + "</thead><tbody>";
            $.each(json, function(_, value){
                state = value.state=="online" ? "rgb(28, 184, 65)" : "rgb(255,0,0)";
                content += "<tr><td>" + value.id + "</td>"
                    + "<td>" + value.addr + "</td>"
                    + "<td><a href=\"/api/redis/" +name+ "/debug/" + value.debug_var_addr + "\">" + value.debug_var_addr + "</a></td>"
                    + "<td><span style=\"background-color:" + state + "; color: white; font-weight:bold; padding:3px\">" + value.state + "</span></td>"
                    + "<td><button proxy-id=\""+value.id+"\" class=\"button-fix button-good pure-button fn-proxy-online\"><i class=\"fa fa-arrow-up\"></i></button>"
                    + "</td></tr>";
            });
            content += "</tbody></table>";
            $(container).append(content);
        }).fail(function(e){
            console.log('get proxy list error! ' + e.responseText);
            loki.notify("get proxy list error!", "error");
        });
    };

    function renderChart(){
        var container = loki.redis_qpsChart,
            pick_ops = loki.redis_qpsChart_pickops;
        $(container).empty();
        chart.drawChart($(container), {
            chart: {
                type: 'line',
                animation: Highcharts.svg,
                marginRight: 10,
                events: {
                    load: function(event) {
                        var sery = this.series[0];
                        clearInterval(loki.chartTimer);
                        loki.chartTimer = setInterval(function () {
                            var x = (new Date()).getTime(),
                                y = ($(pick_ops).text() == 'NA') ? 0 : parseInt($(pick_ops).text()),
                                shift = (sery.data.length<60) ? false : true;
                            sery.addPoint([x, y], true, shift);
                        }, loki.overviewInterval);
                    },
                }
            },
            series: [{name: 'QPS', data: []}],
            legend: {enabled: false}
        });
    };

    function slotListener(){
        $("#slotView").off("click");
        $("#slotView").on("click", ".button-refresh", function(){
            renderSlot();
            renderMigrateTask(false);
        });
        // Set slot listener
        $("#slotView").on("click", ".fn-set-slot", function(){
            loki.setSlotModal = $('.set-slot-modal').modal();
            $('.set-slot-modal .body #from-id').focus();
        });
        // set-slot-modal listener need remove listener first
        $('.set-slot-modal').off('submit');
        $('.set-slot-modal').on('submit', '.set-slot-form', function(e) {
            e.preventDefault();
            var slot_from = $('.set-slot-modal .body #from-id').val(),
                slot_to = $('.set-slot-modal .body #to-id').val(),
                group_id = $('.set-slot-modal .body #group-id').val();
            loki.setSlotModal.modal('hide');
            $('.set-slot-modal .body input').val('');
            var name = loki.getParams().name;
            $.ajax({
                url: "/api/redis/"+name+"/slots",
                type: "POST",
                data: JSON.stringify({
                    from: new Number(slot_from),
                    to: new Number(slot_to),
                    new_group: new Number(group_id)
                }),
                dataType: "text"
            }).done(function(){
                renderSlot();
            }).fail(function(e){
                console.log('set slots error! ' + e.responseText);
                loki.notify("set slots error!", "error");
                renderSlot();
            });
        });

        // Migrate slot listener
        $("#slotView").on("click", ".fn-migrate-slot", function(){
            loki.migrateSlotModal = $('.migrate-slot-modal').modal();
            $('.migrate-slot-modal .body #from-id').focus();
        });
        // migrate-slot-modal listener need remove listener first
        $('.migrate-slot-modal').off('submit');
        $('.migrate-slot-modal').on('submit', '.migrate-slot-form', function(e) {
            e.preventDefault();
            var slot_from = $('.migrate-slot-modal .body #from-id').val(),
                slot_to = $('.migrate-slot-modal .body #to-id').val(),
                group_id = $('.migrate-slot-modal .body #group-id').val(),
                delay = $('.migrate-slot-modal .body #delay').val();
            var name = loki.getParams().name;
            loki.migrateSlotModal.modal('hide');
            $('.migrate-slot-modal .body input').val('');
            $.ajax({
                   url: "/api/redis/"+name+"/migrate",
                   type: "POST",
                   data: JSON.stringify({
                       from: new Number(slot_from),
                       to: new Number(slot_to),
                       new_group: new Number(group_id),
                       delay: new Number(delay)
                   }),
                   dataType: "text"
            }).done(function(){
                renderMigrateTask(true);
            }).fail(function(e){
                console.log('migrate slot error! ' + e.responseText);
                loki.notify("migrate slot error!", "error");
            }).always(function(e){
                renderSlot();
            });
        });
    };

    function renderSlot() {
        var name = loki.getParams().name,
            container = loki.redis_slotChart;
        $(container).empty();
        $.ajax({
            url: "/api/redis/"+name+"/slots",
            type: "GET",
            dataType: "json"
        }).done(function(json_data){
            json_data.sort(function(a,b){
                return parseInt(a.sort_order) - parseInt(b.sort_order)
            });

            // Here we create sery data for highchart
            var chart_height = 140;
            real_series = []
            $.each(json_data, function(_, a_group){
                var tmp = {
                    name: 'group_'+a_group.group_id,
                    stack: 'stack1',
                    data: []
                };
                $.each(['offline','migrating','online'], function(ind, state){
                    $.each(a_group[state], function(_, a_data){
                        tmp.data.push({
                            x: ind,
                            low: a_data[0],
                            high: a_data[1]
                        });
                        if(ind < 2){
                            chart_height = 220;
                        }
                    });
                });
                real_series.push(tmp);
            });

            // Set chart height properly
            if(json_data.length > 16){
                chart_height = 320;
            }
            if(chart_height < 320 && json_data.length > 5){
                chart_height = 220;
            }
            chart_height = chart_height.toString() +'px';

            doDraw(chart_height, real_series);
        }).fail(function(e){
            console.log('get slots error! ' + e.responseText);
            loki.notify("get slots error!", "error");
        });
        var doDraw = function(height, series){
            $(container).css('height', height);
            chart.drawChart($(container), {
                chart: {
                    type: 'columnrange',
                    inverted: true,
                    animation: Highcharts.svg,
                },
                xAxis: {
                    categories: ['Offline Slot','Migrating Slot','Online Slot'],
                    labels: {align: "right"}
                },
                plotOptions: {
                    columnrange: {
                        dataLabels: {
                            enabled: false,
                            formatter: function () {return this.y;},
                        },
                        minPointLength: 10,
                        grouping: false,
                    },
                },
                yAxis: {min: -10, max: 1023, title: {text: 'slot id', x: -1}},
                series: series,
            });
        };
    };

    function renderMigrateTask(renderslot_tag) {
        var name = loki.getParams().name,
            interval = loki.migrateviewInterval,
            container = loki.redis_migrateTask;
            refresh_tag = true;
        if(!name) {
            clearTimeout(loki.renderMigrateTaskTimer);
            return;
        }

        var drawMigrate = function(data){
            $(container).empty();
            if (data == 'null' || data == null){return;}
            if (data != 'null' && data.length > 0){
                var content = "<table class=\"pure-table pure-table-horizontal\"><thead>"
                    + "<tr><th>slot_id</th><th>new_group</th><th>delay</th><th>create_at</th><th>percent</th><th>status</th></tr>"
                    + "</thead><tbody>";
                $.each(data, function(_, slot){
                    content += "<tr><td>" + slot.slot_id + "</td>"
                        + "<td>" + slot.new_group + "</td>"
                        + "<td>" + slot.delay + "</td>"
                        + "<td>" + new Date(slot.create_at * 1000).toLocaleString() + "</td>"
                        + "<td>" + slot.percent + "</td>"
                        + "<td>" + slot.status + "</td>";
                });
                content += "</tbody></table>";
                $(container).append(content);
            }
        };

        $.ajax({
            url: "/api/redis/"+name+"/migrate/tasks",
            type: "GET",
            dataType: "json",
            timeout: interval/5
        }).done(function(data){
            if(!data || data.length == 0){
                refresh_tag = false;
            }
            drawMigrate(data);
        }).fail(function(e){
            console.log("get migrate task error! " + e.responseText);
        }).always(function(){
            clearTimeout(loki.renderMigrateTaskTimer);
            if(refresh_tag){
                loki.renderMigrateTaskTimer = setTimeout(function(){
                    renderMigrateTask(true);
                }, interval);
            }else if(renderslot_tag){
                renderSlot();
            }
        });
    };

    function groupListener() {
        $("#groupView").off("click");
        $("#groupView").on("click", ".button-refresh", function(){
            console.log("debugcc");
            renderGroup();
        });

        // Add group button
        $("#groupView").on("click", ".fn-add-group", function(){
            loki.addGroupModal = $('.add-group-modal').modal();
            $('.add-group-modal .body input').focus();
        });
        // Add group submit. Model should delete listener first
        $('.add-group-modal').off('submit');
        $('.add-group-modal').on('submit', ".add-group-form", function(e) {
            e.preventDefault();
            var group_id = $('.add-group-modal .body input').val();
            var name = loki.getParams().name;
            loki.addGroupModal.modal('hide');
            $('.add-group-modal .body input').val('');
            $.ajax({
                   url: "/api/redis/"+name+"/server_groups/addGroup",
                   type: "POST",
                   data: JSON.stringify({id: new Number(group_id)}),
                   dataType: "text"
            }).done(function(){
                renderGroup();
            }).fail(function(e){
                console.log('add group error! ' + e.responseText);
                loki.notify("add group error!", "error");
                renderGroup();
            });
        });

        // Delete group button
        $('#groupView').on('click', '.fn-delete-group', function(){
            var group_id = $(this).parentsUntil(".group-id").parent().attr('group-id');
            var name = loki.getParams().name;
            if(confirm("确定 "+name+" 删除 group_"+group_id+" 吗？")){
                $.ajax({
                       url: "/api/redis/"+name+"/server_groups/"+group_id,
                       type: "DELETE"
                }).done(function(){
                    renderGroup();
                }).fail(function(e){
                    console.log('delete group error! ' + e.responseText);
                    loki.notify("delete group error!", "error");
                    renderGroup();
                });
            }
        });

        // Add redis button
        $("#groupView").on("click", ".fn-add-redis", function(){
            var group_id = $(this).parentsUntil(".group-id").parent().attr('group-id');
            $('.add-redis-modal .body #group-id').val(group_id);
            $('.add-redis-modal .body #redis-addr').val('');
            loki.addRedisModal = $('.add-redis-modal').modal();
            $('.add-redis-modal .body #redis-addr').focus();
        });
        // Add redis submit. Modal should delete listener firstly
        $('.add-redis-modal').off('submit');
        $('.add-redis-modal').on('submit', '.add-redis-form', function(e) {
            e.preventDefault();
            var group_id = $('.add-redis-modal .body #group-id').val(),
                redis_addr = $('.add-redis-modal .body #redis-addr').val();
            var name = loki.getParams().name;
            loki.addRedisModal.modal('hide');
            $('.add-redis-modal .body input').val('');
            $.ajax({
                   url: "/api/redis/"+name+"/server_groups/"+group_id+"/addServer",
                   type: "POST",
                   data: JSON.stringify({"addr": redis_addr, "type": "slave", "group_id": new Number(group_id)}),
                   dataType: "text"
            }).done(function(){
                renderGroup();
            }).fail(function(){
                console.log('add server error! ' + e.responseText);
                loki.notify("add server error!", "error");
                renderGroup();
            });
        });

        // Delete redis button
        $('#groupView').on('click', '.fn-delete-redis', function(){
            var redis_addr = $(this).parent().parent().children().eq(0).text(),
                redis_type = $(this).parent().parent().children().eq(1).text(),
                group_id = $(this).parentsUntil(".group-id").parent().attr('group-id');
            var name = loki.getParams().name;
            if (confirm("确定 "+name+" 从 group_"+group_id+" 里删除 "+redis_addr+" 吗？")){
                $.ajax({
                       url: "/api/redis/"+name+"/server_groups/"+group_id+"/removeServer",
                       type: "POST",
                       data: JSON.stringify({"addr": redis_addr, "type": redis_type, "group_id": new Number(group_id)}),
                       dataType: "text"
                }).done(function(){
                    renderGroup();
                }).fail(function(e){
                    console.log('remove server error! ' + e.responseText);
                    loki.notify("remove server error!", "error");
                    renderGroup();
                });
            }
        });

        // Promote slave button
        $('#groupView').on('click', '.fn-promote-master', function(){
            var redis_addr = $(this).parent().parent().children().eq(0).text(),
                redis_type = $(this).parent().parent().children().eq(1).text(),
                group_id = $(this).parentsUntil(".group-id").parent().attr('group-id');
            var name = loki.getParams().name;
            $.ajax({
                url: "/api/redis/"+name+"/server_groups/"+group_id+"/promote",
                type: "POST",
                data: JSON.stringify({"addr": redis_addr, "type": redis_type, "group_id": new Number(group_id)}),
                dataType: "text"
            }).done(function(){
                renderGroup();
            }).fail(function(e){
                console.log('promote server error! ' + e.responseText);
                loki.notify("promote server error!", "error");
                renderGroup();
            });
        });
    };

    function renderGroup() {
        var name = loki.getParams().name,
            container = loki.redis_groupContent;
        $(container).empty();
        $.ajax({
            url: "/api/redis/"+name+"/server_groups",
            type: "GET",
            dataType: "json"
        }).done(function(msg){
            msg.sort(function(a,b){
                return parseInt(a.id) - parseInt(b.id)
            });
            $.each(msg, function(_, group){
                var content = "<div class=\"group-id\" group-id=\""+group.id+"\"><div class=\"subtitle\">group_" + group.id
                    + "<div class=\"action-button\">"
                    + "<button class=\"button-auto pure-button fn-add-redis\"><i class=\"fa fa-plus\"></i>Add Redis</button>"
                    + "<button class=\"button-fix button-bad pure-button fn-delete-group\"><i class=\"fa fa-close\"></i></button>"
                    + "</div></div>"
                    + "<table class=\"pure-table pure-table-horizontal\">"
                    + "<thead><tr><th style=\"width:24%\">Addr</th><th style=\"width:8%\">Type</th><th style=\"width:18%\">Mem Used</th><th style=\"width:40%\">Keys</th><th style=\"width:10%\">Action</th></tr>"
                    + "</thead><tbody>";
                $.each(["master","slave","offline"], function(_, serv_type){
                       if(serv_type in group){
                        $.each(group[serv_type], function(_, serv){
                            content += "<tr><td>"+serv.serv_addr+"</td><td>"
                                + serv_type + "</td><td>"
                                + readableByte(serv.used_memory) + " / " + readableByte(serv.maxmemory) + "</td><td>"
                                + ('db0' in serv ? serv.db0 : '') + "</td><td>"
                                + "<button class=\"button-fix button-good pure-button pure-u-1-2 "
                                + (serv_type=="master"?"pure-button-disabled":"fn-promote-master") + "\"><i class=\"fa fa-arrow-up\"></i></button>"
                                   + "<button class=\"button-fix button-bad pure-button pure-u-1-2 "
                                   + (serv_type=="master"?"pure-button-disabled":"fn-delete-redis") + "\"><i class=\"fa fa-close\"></i></button>"
                                   + "</td></tr>";
                        })
                    }
                });
                content += "</tbody></table></div>";
                $(container).append(content);
            });
        }).fail(function(e){
            console.log('get server groups error! ' + e.responseText);
            loki.notify("get server groups error!", "error");
        });
    };

    // Render the codis panel
    function renderCodis() {
        var container = $(".container .container-detail");
        // Siblings is .main
        container.siblings().hide();
        container.show();

        // Global auto refresh interval
        loki.overviewInterval = 2000;
        loki.migrateviewInterval = 10000;
        loki.redis_overviewContent = "#overview > .content";
        loki.redis_proxyContent = "#proxyView > .content";
        loki.redis_qpsChart = "#overviewChart > .content";
        loki.redis_qpsChart_pickops = "#overview dd:eq(4)";
        loki.redis_slotChart = "#slotView > .content:eq(0)";
        loki.redis_migrateTask = "#slotView > .content:eq(1)";
        loki.redis_groupContent = "#groupView > .content";
        
        renderOverview();
        renderProxy();
        renderSlot();
        renderMigrateTask(false);
        renderGroup();
        renderChart();
    };
    loki.run();
});
