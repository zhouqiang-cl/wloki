define([
    'jquery',
    'underscore',
    'handlebars',
], function($, _, Handlebars) {
    Handlebars.registerHelper('times', function(n, block) {
        var accum = '';
        for(var i = 0; i < n; ++i)
            accum += block.fn(i);
        return accum;
    });
    Handlebars.registerHelper('times_one', function(n, block) {
        var accum = '';
        for(var i = 0; i < n; ++i)
            accum += block.fn(i + 1);
        return accum;
    });
    Handlebars.registerHelper('ifeq', function(v1, v2, options) {
        if(v1 == v2)
            return options.fn(this);
        return options.inverse(this);
    });

    /*jshint multistr: true */
    var template_string = '\
        <div class="info">Total: {{total}}, {{limit}} entries per page.</div>\
        <ul>\
            {{#times_one pages}}\
            <li class="{{#ifeq this ../index}}active{{/ifeq}}">\
                <a href="#" data-index="{{this}}">{{this}}</a>\
            </li>\
            {{/times_one}}\
        </ul>\
        ',
        template = Handlebars.compile(template_string);

    var Paginator = function(el, page_renderer, keymap, data) {
        /* page_renderer(index) -> Promise */
        /*
            keymap: {
                index: 'key1',
                total: 'key2',
                limit: 'key3',
                pages: 'key4',
            }
        */

        var _this = this;

        this.el = el.addClass('the-paginator');
        this.page_renderer = page_renderer;
        this.keymap = keymap;

        // Bind events
        this.el.on('click', 'li>a', function(e) {
            e.preventDefault();
            var $this = $(e.currentTarget),
                to_index = $this.attr('data-index');

            _this.processing(true);
            _this.page_renderer(to_index).then(function() {
                _this.processing(false);
            });
        });

        if (data)
            this.render(data);
    };

    _.extend(Paginator.prototype, {
        update: function(data) {
            var _this = this,
                keymap = this.keymap;
            for (var k in keymap) {
                if (!keymap.hasOwnProperty(k))
                    continue;
                var mapped = keymap[k],
                    v = data[mapped];
                if (v === undefined) {
                    console.error('Could not get %s by key %s in data %o', k, mapped, data);
                } else {
                    _this[k] = v;
                }
            }
        },
        render: function(data) {
            this.update(data);
            var inner_html = template(this);
            this.el.html(inner_html);
        },
        processing: function(flag) {
            if (flag)
                this.el.css('pointer-events', 'none');
            else
                this.el.css('pointer-events', 'auto');
        },
    });

    return Paginator;
});
