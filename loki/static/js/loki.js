define([
    'humane',
    'jquery',
    'jquery-history',
    'util/alfred',
    'util/qatrix',
    'util/datetime',
    'jstree',
    'jquery-modal',
    'util/jquery-extra',
    'util/builtin-extend'
], function(humane, $, History, alfred, qatrix, datetime) {

    /* Define LOKI namespace */

    var LOKI = window.loki = {
        sidebar_inited: false,
        ptree_loaded: false,
        sidebar: 'ptree',  // or 'domains', or `undefined` if you don't want it.
        ptree_config: {
            mode: 'disable',
            levels: []
        },

        $ptree: $('#ptree'),
        $domains: $('#domains'),

        ptree_promise: undefined,

        tabs: undefined,
        // If `LOKI.tabs` is defined,
        // `_tab_initializers` and `_tab_handlers` are required to be defined
        _tab_handlers: undefined,
        _tab_initializers: undefined,

        _params_handler: undefined,
        _tab_params_handler: undefined,

        _ready_func: undefined,

        _events: {},
        enabled_nodes: [],
        // When false, use /api/nodes to get all nodes,
        // when true, use /api/nodes/user_nodes to get user available nodes
        restrict_nodes: false,
    };




    /* LOKI run flow:
     * 0. Application js call `loki.run()`
     * 1. Bind tab click: initTabs()
     * 2. Bind url change: initRouter()
     * 3. Initialize sidebar: initSidebar()
     * 4. dispatchParams() being called explictly
     * 5. Render tab by params: gotoTab()
     */

    // 1
    var initTabs = function() {
        $('.tabs > ul > li > a').on('click', function(e) {
            e.preventDefault();

            var tab = $(e.currentTarget).attr('alt').split('-')[1],
                prev_tab = getParams().tab;

            route_params({tab: tab});
        });
    },


    // 2
    initRouter = function() {
        History.Adapter.bind(window,'statechange',function(){
            // var State = History.getState();
            // console.log('[ history ] statechange', State);
            dispatchParams();
        });

        dispatchParams();
    },


    // 3
    initSidebar = function(params, callback) {
        var sidebar = $('#sidebar'),
            body = $('body');
        console.info('[ loki ] @3 init sidebar');

        if (LOKI.sidebar == 'ptree') {
            // Init ptree
            initPTree(function() {
                // Finally, call callback after all PTree stuffs are done.
                callback();

                // Init alfred
                if (!alfred.is_enabled())
                    alfred.enable_alfred(
                        $('.alfred'),
                        // Data retriever
                        function() {
                            return LOKI.enabled_nodes;
                        },
                        // On select callback
                        function(nid) {
                            route_params({nid: nid});
                        }
                    );
            });

            // Bind search button
            $('#sidebar .fn-search').on('click', function() {
                alfred.toggle_alfred();
            });

            // Bind collapse button
            sidebar.find('.fn-collapse').click(function() {
                if (body.hasClass('sidebar-collapsed')) {
                    body.removeClass('sidebar-collapsed');
                    $(this).siblings().show();
                    $(this).find('i').removeClass('fa-angle-right').addClass('fa-angle-left');
                } else {
                    body.addClass('sidebar-collapsed');
                    $(this).siblings().hide();
                    $(this).find('i').removeClass('fa-angle-left').addClass('fa-angle-right');
                }
                // Trigger resize to make highcharts resize
                $(window).trigger('resize');
            });

        } else if (LOKI.sidebar == 'domains') {
            renderDomains(params.did);

        } else {
            console.info('No sidebar or invalid: LOKI.sidebar =' + LOKI.sidebar);
            // sidebar.empty();
            // return false;
        }

        LOKI.sidebar_inited = true;
    },


    initPTree = LOKI.initPTree = function(callback) {
        fetchPTree(function(data) {
            var $ptree = LOKI.$ptree;

            // Reformat data
            data = reformatNodes(data);

            // Render PTree
            renderPTree($ptree, data, callback);

            // Bind on select ptree
            $ptree.on("select_node.jstree", function (e, data) {
                console.info('on select_node.jstree');
                if (!data.node) {
                    console.error('selected jstree node has no data, url not changed', data);
                    return;
                }

                var nid = data.selected[0];
                LOKI.current_node = data.node;
                $('#sidebar .selected-node > .info > span').html(data.node.text);
                console.warn('Route in selecte_node.jstree', nid);
                route_params({nid: nid});
            });

            // Bind on reconfigure
            $ptree.on('reconfigure', function(e, options) {
                reconfigurePTree(options);
            });
        });
    },



    // 4
    dispatchParams = LOKI.dispatchParams = function() {
        /*
        dispatchParams will call:
        - initSidebar
        - initPTree (inside initSidebar)
        */
        var params = getParams();

        // Check params state
        LOKI.params_state = checkParamsChanges(params);

        if (LOKI._params_handler) {
            console.info('[ loki ] @4 call params handler');
            LOKI._params_handler(params);
        }

        var $ptree = LOKI.$ptree;

        // The real works being done
        var _dispatchParams = function() {
            console.info('[ loki ] @4 dispatch params', params);

            // Reset ptree_promise
            LOKI.ptree_promise = $.Deferred();

            if (LOKI.sidebar == 'ptree') {
                affectPTree(params);
            }

            if (LOKI.tabs) {
                // Go to tab & run initializer & handler
                gotoTab(params.tab, params);
            }
        };

        if (LOKI.sidebar_inited) {
            if (LOKI.sidebar == 'ptree' && !LOKI.ptree_loaded) {
                console.log('@4 sidbar is ptree and is not loaded');
                // Reload ptree then dispatch
                reloadPTree(_dispatchParams);
            } else {
                // Directly dispatch
                _dispatchParams();
            }
        } else {
            initSidebar(params, _dispatchParams);
        }
    },


    // 5
    gotoTab = function(tab, params) {
        /*
        Requires `LOKI._tab_initializers` defined globally
        */

        var currentTab = $('.tabs > ul > li.active > a'),
            tabName = getTabName(tab),
            is_switched = false;

        if (currentTab.length && currentTab.attr('alt').split('-')[1] == tab)
            is_switched = true;

        // If not switched, switch to tab and run initializer
        if (!is_switched) {
            if (tab === undefined)
                tab = '1';
            var allTabs = $('.tabs > ul > li'),
                thisTab = $('.tabs > ul > li > a[alt="#tab-' + tab + '"]').parent(),
                allContents = $('.tabs > div'),
                thisContent = $('#tab-' + tab);

            // console.log('tabName', tabName, tab);

            // Tabs UI
            allTabs.removeClass('active');
            thisTab.addClass('active');

            // Contents UI
            allContents.hide();
            thisContent.show();

            // Run initializers
            var initializer = LOKI._tab_initializers['init' + tabName];
            if (!initializer.executed) {
                console.info('[ tab ] Initializing', tabName);
                initializer();
                initializer.executed = true;
            }
        }

        // Run handler afterwards
        if (LOKI._tab_handlers === undefined) {
            console.log('No `_tab_handlers` defined, skip');
            return;
        }

        var handler = LOKI._tab_handlers['handle' + tabName];

        if (handler === undefined) {
            console.log('No handler for tab ' + tabName + 'defined, skip');
        } else {
            console.info('[ tab ] Handling', tabName, params);
            handler(params);
        }

        if (LOKI._tab_params_handler) {
            console.info('[ loki ] call tab params handler');
            LOKI._tab_params_handler(params);
        }

        return tabName;
    };

    /* End LOKI run flow */



    /* LOKI control functions */

    $.extend(LOKI, {
        configure: function(options) {
            $.honest_extend(LOKI, options);
        },

        ready: function(func) {
            LOKI._ready_func = func;
        },

        run: function() {
            /* run will acturally run after document is ready */
            $(function() {
                console.log('[ loki ] loki.run()');

                if (LOKI._ready_func)
                    LOKI._ready_func();

                if (LOKI.tabs)
                    initTabs();

                initRouter();

                initNav();
                // disableNumberInputScroll();
            });
        },

        defineTabHandlers: function(obj) {
            LOKI._tab_handlers = obj;
        },

        defineTabInitializers: function(obj) {
            LOKI._tab_initializers = obj;
        },

        defineParamsHandler: function(func) {
            LOKI._params_handler = func;
        },

        defineTabParamsHandler: function(func) {
            LOKI._tab_params_handler = func;
        },

        trigger: function(event) {
            /*
            Event dispatcher
            */
            if (event in LOKI._events) {
                var args = Array.prototype.slice.call(arguments);
                LOKI._events[event].apply(null, args.slice(1));
            }
        },

        on: function(event, func) {
            if (typeof event === 'object') {
                $.honest_extend(LOKI._events, event);
            } else {
                LOKI._events[event] = func;
            }
        }
    });




    /* Router */

    var checkParamsChanges = function(params) {
        var params_state = {
            nid: {
                initial: false,
                changed: false
            },
            tab: {
                initial: false,
                changed: false
            },
            rid: {
                initial: false,
                changed: false
            },
            initial: false
        };

        if (!LOKI._last_params) {
            LOKI._last_params = params;
            params_state.initial = true;
            params_state.nid.initial = true;
            params_state.tab.initial = true;
            params_state.rid.initial = true;
            return params_state;
        }
        var _last_params = LOKI._last_params;
        LOKI._last_params = params;
        // nid
        if (_last_params.nid != params.nid) {
            LOKI.trigger('nid_change', _last_params.nid, params.nid);
            params_state.nid.changed = true;
        }
        // tab
        if (_last_params.tab != params.tab) {
            LOKI.trigger('tab_change', _last_params.tab, params.tab);
            params_state.tab.changed = true;
        }
        // rid
        if (_last_params.rid != params.rid) {
            LOKI.trigger('rid_change', _last_params.rid, params.rid);
            params_state.rid.changed = true;
        }
        return params_state;
    },


    route = LOKI.route = function(params, force_dispatch) {
        var paramString;
        if (typeof params == 'object') {
            if ($.isEmptyObject(params))
                paramString = '';
            else
                paramString = '?' + $.param(params);
        } else {
            paramString = params;
        }
        var uri = window.location.pathname + paramString,
            current_uri = window.location.pathname + window.location.search;

        console.log('[ loki.route ] current uri', current_uri, 'next uri', uri);
        if (current_uri == uri) {
            if (force_dispatch) {
                console.info('[ loki.route ] force dispatch');
                dispatchParams();
            }
        } else {
            History.pushState({}, document.title, uri);
        }
    },


    _tab_view_params = ['nid', 'tab', 'rid'],


    route_params = LOKI.route_params = function(options, force_dispatch) {
        /* For tab view params, reconstruct `params` according to their hierarchy,
         * for other params, only change the passed params for current url */
        var params = getParams();

        if ('nid' in options) {
            if (options.nid)
                params.nid = options.nid;
            else
                delete params.nid;

            delete params.rid;
        }
        if ('tab' in options) {
            if (options.tab)
                params.tab = options.tab;
            else
                delete params.tab;

            delete params.rid;
        }
        if ('rid' in options) {
            if (options.rid)
                params.rid = options.rid;
            else
                delete params.rid;
        }

        for (var k in options) {
            if (!(k in _tab_view_params)) {

                if (options[k] === undefined)
                    delete params[k];
                else
                    params[k] = options[k];
            }
        }
        console.info('[ loki ] Route params', params);

        route(params, force_dispatch);
    },


    parseParams = function(search) {
        return JSON.parse('{"' + decodeURIComponent(search.replace('+', ' ')).replace(/"/g, '\\"').replace(/&/g, '","').replace(/=/g,'":"') + '"}');
    },


    getParams = LOKI.getParams = function() {
        var search = location.search.substring(1);
        if (search) {
            return parseParams(search);
        } else {
            return {};
        }
    },


    getParameterByName = function(name) {
        name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
        var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
            results = regex.exec(location.search);
        return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    };


    /* PTree */

    var fetchPTree = LOKI.fetchPTree = function(cb, async) {
        if (async === undefined) async = true;

        var url;
        if (LOKI.restrict_nodes) {
            url = '/api/nodes/user_nodes?with_path=1';
        } else {
            url = '/api/nodes?with_path=1';
        }

        $.ajax({
            url: url,
            type: 'GET',
            async: async,
            success: function(data) {
                cb(data.data);
            }
        });
    },


    renderPTree = LOKI.renderPTree = function($ptree, data, callback) {
        /*
        After renderPTree has called, ptree should has no selection,
        that means, its idempotent.
        */
        var jstree = $ptree.jstree(true),
            done_event = jstree ? 'refresh.jstree' : 'ready.jstree';
        // console.log('renderPTree', jstree, done_event);

        $ptree.one(done_event, function() {
            console.log('[ ptree ] renderPTree: on ' + done_event + ', doing callback');
            callback();

            LOKI.ptree_loaded = true;

            LOKI.trigger('ptree_loaded');
        });

        if (jstree) {
            jstree.deselect_all();
            jstree.settings.core.data = data;
            jstree.refresh();

        } else {
            // First time, do init stuffs
            $ptree.show();

            $ptree.jstree({
                "core" : {
                    //"animation": 0,
                    "check_callback": true,
                    //"themes": {"stripes" : true},
                    'data': data,
                    multiple: false
                },
                "types": {
                    "default" : {
                        "icon" : "fa fa-leaf",
                    },
                    "root" : {
                        "icon" : "fa fa-dot-circle-o",
                    },
                    "bottom": {
                        "icon": "fa fa-cubes"
                    }
                },
                plugins: ['types', 'search', 'sort']
            });
        }
    },


    selectPTree = LOKI.selectPTree = function(node_id) {
        if (!node_id)
            return;

        var jstree = LOKI.$ptree.jstree(true),
            node = jstree.get_node(node_id),
            selected_node_id = jstree.get_selected()[0];
        console.log('[ ptree ] selectPTree: from', selected_node_id, 'to', node_id);

        if (selected_node_id != node_id) {
            if (selected_node_id)
                jstree.deselect_node(selected_node_id, undefined, undefined, undefined, true);

            // Pass `no_trigger` true to the function
            jstree.select_node(node, undefined, undefined, undefined, true);

            // Scroll sidebar
            var $node = jstree.get_node(node, true),
                $content = $('#sidebar .content'),
                relative_offset_top = $node.offset().top + $content.scrollTop(),
                shift = 100,
                scroll_top = relative_offset_top - 100;
            // console.log('scroll top', $node, scroll_top);
            $('#sidebar > .content').animate({
                scrollTop: scroll_top
            }, 300);
        }

        if (node.state.disabled) {
            console.warn('Select a disabled node');
        }
    },


    affectPTree = function(params) {
        var $ptree = LOKI.$ptree,
            params_state = LOKI.params_state,
            ptree_config = getPTreeConfig(params.tab);
        console.info('[ ptree ] affect ptree', params);
        // console.log('ptree state', JSON.stringify(params_state));

        // Update ptree_config by tab
        LOKI.ptree_config = ptree_config;

        // - Reconfigure
        if (params_state.initial || params_state.tab.changed) {
            LOKI.$ptree.trigger('reconfigure', ptree_config);
        }

        // - Select node
        $ptree.jstree(true).open_node('1');
        if (params.nid) {
            selectPTree(params.nid);
        }

        LOKI.ptree_promise.resolve();
    },


    reloadPTree = LOKI.reloadPTree = function(callback) {
        console.info('reload ptree');
        fetchPTree(function(data) {
            var $ptree = LOKI.$ptree;

            // Reformat data
            data = reformatNodes(data);

            // Render PTree
            renderPTree($ptree, data, callback);
        });
    },


    reloadPTreeThenAffect = LOKI.reloadPTreeThenAffect = function() {
        /*
        Reload ptree then affect ptree with current params, used when a refresh
        without selection change on ptree is needed
        */
        reloadPTree(function() {
            affectPTree(getParams());
        });
    },


    getPTreeConfig = function(tab) {
        if (!LOKI.tabs) {
            return LOKI.ptree_config;
        }
        var tabName = getTabName(tab);
        config = LOKI.ptree_tab_configs ? LOKI.ptree_tab_configs[tabName] : LOKI.ptree_config;
        return config;
    },


    _getNodeAnchor = function(node) {
        var node_dom = document.getElementById(node.id);
        if (node_dom) {
            return node_dom.getElementsByClassName('jstree-anchor')[0];
        } else {
            return undefined;
        }
    },


    disableNode = function(node) {
        node.state.disabled = true;
        var node_anchor = _getNodeAnchor(node);
        if (!node_anchor) return;
        qatrix.$className.add(node_anchor, 'jstree-disabled');
        // console.log('disable node', node.id);
    },


    enableNode = function(node) {
        node.state.disabled = false;
        var node_anchor = _getNodeAnchor(node);
        if (!node_anchor) return;
        qatrix.$className.remove(node_anchor, 'jstree-disabled');
        // console.log('enable node', node.id);
    },


    reconfigurePTree = function(options) {
        /*
        options: {
            mode: 'disable'  // 'enable'
            levels: [0, 1]  // [-1, -2]
        }
        */

        var $ptree = LOKI.$ptree,
            jstree = $ptree.jstree(true),
            t1, t2,
            __,
            enabled_nodes = [];

        t1 = new Date().getTime();
        // console.log('options', options);
        for (var id in jstree._model.data) {
            if (id == '#')
                continue;

            var node = jstree._model.data[id],
                disabled = node.state.disabled,
                level = node.original.level,
                negative_level = node.original.negative_level,
                is_in_level = (options.levels.contains(level) || options.levels.contains(negative_level)),
                flag = options.mode == 'disable' ? is_in_level : !is_in_level;

            switch (options.mode) {
                case 'disable':
                    if (is_in_level) {
                        if (!disabled) disableNode(node);
                    } else {
                        if (disabled) enableNode(node);
                        enabled_nodes.push(node.original);
                    }
                    break;
                case 'enable':
                    if (is_in_level) {
                        if (disabled) enableNode(node);
                        enabled_nodes.push(node.original);
                    } else {
                        if (!disabled) disableNode(node);
                    }
                    break;
                default:
                    console.error('wrong ptree_config mode', options.mode, options);
            }
        }
        t2 = new Date().getTime();
        console.debug('[ ptree ] Execution time of reconfigurePTree: ', t2 - t1, options);

        LOKI.enabled_nodes = enabled_nodes;
    },


    getNodeNegLevel = function (node, context) {
        if (node.negative_level === 0) {
            var node_path = node.path + '/';
            var neg_level = Math.min(context.nodes_array[node.level+1].filter(
                function(el) {return (el.path.lastIndexOf(node_path, 0) === 0);}
            ).map(
                function(el) {return getNodeNegLevel(el, context);}
            )) - 1;
            node.negative_level = neg_level;
        }
        return node.negative_level;
    },


    reformatNodes = function(all_nodes) {
        var node_map = {},
            nodes_array = [[],[],[],[],[],[],[],[],[],[],[]];

        var t1 = new Date().getTime();
        var context = {};

        all_nodes.forEach(function(n) {
            n.level = (n.path.match(/\//g)).length - 1;
            n.negative_level = 0;
            nodes_array[n.level].push(n);
            node_map[n.path] = n;
        });
        context.nodes_array = nodes_array;
        context.nodes_map = node_map;
        nodes_array.forEach(function(array) {
            array.forEach(function (node) {
                if (node.negative_level === 0)
                    getNodeNegLevel(node, context);
            });
        });
        var t2 = new Date().getTime();
        console.debug('[ ptree ] Execution time of reformatNodes:', t2 - t1);
        return all_nodes;
    },


    getCurrentNode = LOKI.getCurrentNode = function() {
        var jstree = LOKI.$ptree.jstree(true),
            selectedNodes = jstree.get_selected();

        if (!selectedNodes.length) {
            console.warn('getCurrentNode: No node selected.');
            return null;
        }
        var _node = jstree.get_node(selectedNodes[0]),
            node = $.extend({}, _node.original);

        node.state = _node.state;

        // console.log('getCurrentNode', _node, node);
        node.parent_id = _node.parent;

        return node;
    };




    /* Tabs */

    var getTabName = function(tab) {
        tab = tab || '1';
        return LOKI.tabs[tab];
    },


    // TODO move these two method to tab-view.js, and make ptree.js use tab-view.js too
    coverTab = LOKI.coverTab = function(tab, words) {
        var content = $('#tab-' + tab),
            cover = content.find('> .cover');
        if (!cover.length) {
            cover = $('<div></div>').addClass('cover');
            content.append(cover);
        }
        cover.html(words);
        cover.show();
    },


    uncoverTab = LOKI.uncoverTab = function(tab) {
        var content = $('#tab-' + tab),
            cover = content.find('> .cover');
        if (!cover.length)
            return;
        cover.hide();
    };




    /* Others */

    var initNav = function() {
        $('header nav > ul .jump-node').on('click', function(e) {
            var uri = this.href,
                nid = getParams().nid;
            if (nid)
                uri += '?nid=' + nid;
            this.href = uri;
        });
    },


    disableSidebar = function() {
        var sidebar = $('#sidebar');
        var cover = $('<div class="sidebar-cover"></div>');
        cover.prependTo(sidebar);
    },


    renderDomains = function (did) {
        var $domains = LOKI.$domains;

        $domains.show();
        $.ajax({
            url: '/api/domains',
            type: 'GET',
        }).then(function(json) {
            var items = $domains.find('.items');
            items.empty();

            json.data.forEach(function(o) {
                var item = $('<li><i class="fa fa-angle-right"></i>' +
                    '<a href="#" class="domain_item">' + o + '</a></li>');
                items.append(item);
            });
        });
    },


    createPanel = LOKI.createPanel = function(options) {
        var panel = $('<div></div>'),
            class_str = 'panel';
        if (options.class_) {
            class_str += ' ' + options.class_;
        }
        panel.attr('class', class_str);

        if (options.attr) {
            panel.attr(options.attr);
        }

        var inner = options.inner;
        if (inner) {
            if ($.isArray(inner)) {
                inner.forEach(function(i) {
                    panel.append(i);
                });
            } else {
                if (typeof inner === 'string') {
                    inner = $(inner);
                }
                panel.append(inner);
            }
        }

        if (options.parent) {
            options.parent.append(panel);
        }
        return panel;
    },


    disableNumberInputScroll = LOKI.disableNumberInputScroll = function() {
        // Disable mousewheel on a input number field when in focus
        // (to prevent Cromium browsers change the value when scrolling)
        $(document).on('focus', 'input[type=number]', function (e) {
            $(this).on('mousewheel.disableScroll', function (e) {
                e.preventDefault();
            });
        });
        $(document).on('blur', 'input[type=number]', function (e) {
            $(this).off('mousewheel.disableScroll');
        });
    },


    registerAjaxError = LOKI.registerAjaxError = function() {
        // Only used for 5xx errors
        $(document).ajaxError(function(evt, jqXHR, context, exception) {
            // FIXIT 504 == RequestError, but not TSDB error
            if (jqXHR.status == 504) {
                notify('OpenTSDB 查询超时，请重试', 'error');
                return;
            }

            if (jqXHR.status < 500)
                return;

            popAjaxError(jqXHR, context);
        });
    },

    popAjaxError = LOKI.popAjaxError = function(jqXHR, context) {
        console.error('pop ajax error', jqXHR, context);

        var $modal = $('.ajax-error-modal');

        // Request: url, method, data
        $modal.find('.value.url').html(context.url);
        $modal.find('.value.method').html(context.type);
        $modal.find('.value.data').html(context.data || 'None');

        // Response: status_code, body
        $modal.find('.value.status').html(jqXHR.status + ' ' + jqXHR.statusText);
        $modal.find('.value._body').html(
            jqXHR.responseText.replace(/</g, '&lt;').replace(/>/g, '&gt;') || 'None');

        $modal.modal();
    },


    testAjaxError = LOKI.testAjaxError = function() {
        $.get('/_test_error');
    },


    notify = LOKI.notify = function(message, type, callback, timeout) {
        // type could be 'info', 'success', 'error'
        type = type || 'success';
        humane.log(
            message,
            {
                addnCls: 'humane-jackedup-' + type,
                timeout: timeout || 3000,
                clickToClose: true
            },
            callback);
    },


    notifyAjaxError = LOKI.notifyAjaxError = function(jqXHR) {
        console.log('ajax error', jqXHR);
        notify(jqXHR.responseText, 'error');
    },


    ajax_error_notify = LOKI.ajax_error_notify = function(xhr) {
        if (xhr.responseJSON && xhr.responseJSON.error && xhr.responseJSON.error.message)
            notify(xhr.responseJSON.error.message, 'error', undefined, 5000);
    };
    // Use this new name
    LOKI.notifyErrorMessage = ajax_error_notify;




    /* For debugging purpose */

    LOKI.on({
        nid_change: function(b, a) {
            // console.log('@on nid change', b, a);
        },
        tab_change: function(b, a) {
            // console.log('@on tab change', b, a);
        },
        rid_change: function(b, a) {
            // console.log('@on rid change', b, a);
        }
    });




    /* Return loki as a module */

    return LOKI;
});
