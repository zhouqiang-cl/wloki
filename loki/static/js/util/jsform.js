/*
 * TODO
 * - split row render into two parts: input render and row render,
 *   so that insert new input lines won't be redundant for arrayinput
 *   and dictinput.
 */

/*
Usage example:

schema = [
    {
        "key": "name",
        "type": "text",
        "label": "名字",
        "value": "guoxuxing",
        "required": true,
        "hidden": false,
        "placeholder": "您的姓名"
    },
    {
        "key": "bio",
        "type": "textarea",
        "label": "介绍",
        "required": true,
        "placeholder": "自我介绍"
    },
    {
        "key": "check_time",
        "type": "select",
        "label": "入职时间",
        "value": 2012,
        "items": [
            {"value":2014, "label":"2014年"},
            {"value":2013, "label":"2013年"},
            {"value":2012, "label":"2012年"}
        ]
    },
    {
        "key": "is_admin",
        "type": "checkbox",
        "label": "管理员",
        "value": true
    },
    {
        "key": "age",
        "type": "number",
        "label": "年龄",
        "value": 21
    },
    {
        "key": "friends",
        "type": "arrayinput",
        "label": "朋友",
        "value": [
            "mengxiao",
            "xiaoyu"
        ]
    },
    {
        "key": "contacts",
        "type": "dictinput",
        "label": "联系方式",
        "items": [
            {"key":"mobile", "value":"12345678"},
            {"key":"home", "value":"99999999"},
        ]
    },
    {
        "key": "alarm_method",
        "type": "multicheckbox",
        "label": "报警方式",
        "items": [
            {"key":"sms", "value":true},
            {"key":"xmpp", "value":false},
            {"key":"email", "value":false},
        ]
    },
];
*/

define([
    'jquery',
    'handlebars'
], function($, Handlebars) {
    var compileTemplates = function(templates) {
        for (var _tpl_k in templates) {
            templates[_tpl_k] = Handlebars.compile(templates[_tpl_k]);
        }
    };

    var templates = {
        text: '<div class="form-row" data-key="{{key}}" data-type="text">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '<input type="text" value="{{value}}">' +
            '</div>',
        number: '<div class="form-row" data-key="{{key}}" data-type="number">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
            '<input type="number" value="{{value}}">' +
            '</div>',
        checkbox: '<div class="form-row" data-key="{{key}}" data-type="checkbox">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '<input type="checkbox" {{#if value}}checked{{/if}} >' +
            '</div>',
        textarea: '<div class="form-row" data-key="{{key}}" data-type="textarea">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
            '<textarea name="{{key}}">' +
            '{{value}}</textarea>' +
            '</div>',
        select: '<div class="form-row" data-key="{{key}}" data-type="select">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
            '<select>' +
            '{{#items}}' +
            '<option value="{{value}}">{{label}}</option>' +
            '{{/items}}' +
            '</select>' +
            '</div>',
        arrayinput: '<div class="form-row" data-key="{{key}}" data-type="arrayinput">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
            '<div class="input-group">' +
            '{{#if value}}' +
            '{{#value}}' +
            '<div><input type="text" value="{{this}}"><button class="fn-remove">-</button></div>' +
            '{{/value}}' +
            '{{else}}' +
            '<div><input type="text"><button class="fn-remove">-</button></div>' +
            '{{/if}}' +
            '</div>' +
            '<button class="fn-add">+</button>' +
            '</div>',
        dictinput: '<div class="form-row" data-key="{{key}}" data-type="dictinput">' +
            '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
            '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
            '<div class="input-group">' +
            '{{#if items}}' +
            '{{#items}}' +
            '<div class="dict-item">' +
            '<input type="text" value="{{key}}" name="key" placeholder="Key">' +
            '<input type="text" value="{{value}}" name="value" placeholder="Value">' +
            '<button class="fn-remove">-</button></div>' +
            '{{/items}}' +
            '{{else}}' +
            '<div class="dict-item">' +
            '<input type="text" name="key" placeholder="Key"><input type="text" name="value" placeholder="Value">' +
            '<button class="fn-remove">-</button></div>' +
            '{{/if}}' +
            '</div>' +
            '<button class="fn-add">+</button>' +
            '</div>',
        //multicheckbox: '<div class="form-row" data-key="{{key}}" data-type="multicheckbox">' +
        //    '<label>{{label}} {{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}</label>' +
        //    '{{#if notice}}<blockquote>{{notice}}</blockquote>{{/if}}' +
        //    '<div class="input-group">' +
        //    '{{#items}}' +
        //    '<span><label>{{label}}</label><input type="checkbox" name="{{key}}" {{#if value}}checked{{/if}}></span>' +
        //    '{{/items}}' +
        //    '</div>' +
        //    '</div>',
    };


    // Compile templates
    compileTemplates(templates);


    var processors = {
        select: function(row, data) {
            row
                .find('option[value="' + data.value + '"]')
                .prop("selected", true);
        },

        arrayinput: function(row, data) {
            row.find('.fn-add').on('click', function(e) {
                e.preventDefault();

                var group = row.find('.input-group');
                if (!group.find('input:last').val())
                    return;
                var item_str = '<div><input type="text">' +
                    '<button class="fn-remove">-</button></div>'
                group.append($(item_str));
            });

            row.on('click', '.fn-remove', function (e) {
                e.preventDefault();

                var input_item = $(this).parent();
                if (input_item.parent().children().length == 1) {
                    input_item.find('input').val("");
                } else {
                    input_item.remove();
                }
            })
        },

        dictinput: function(row, data) {
            row.find('.fn-add').on('click', function(e) {
                e.preventDefault();

                var group = row.find('.input-group');
                if (!group.find('input:last').val())
                    return;
                var item_str = '<div class="dict-item"><input type="text" name="key" placeholder="Key">' +
                    '<input type="text" name="value" placeholder="Value">' +
                    '<button class="fn-remove">-</button></div>'
                group.append($(item_str));
            });

            row.on('click', '.fn-remove', function (e) {
                e.preventDefault();

                var input_item = $(this).parent();
                if (input_item.parent().children().length == 1) {
                    input_item.find('input').val('');
                } else {
                    input_item.remove();
                }
            });
        }
    };


    var renderRow = function(data) {
        var template = templates[data.type],
            row,
            render_data = {};
        $.extend(render_data, data);
        render_data.value = data.value || data.default;

        // Render html
        row = $(template(render_data));

        if (data.readonly) {
            //if (data.type == 'multicheckbox' || data.type == 'checkbox') {
            //    row.find(':input').attr('onclick', 'return false');
            if (data.type == 'checkbox') {
                row.find(':input').attr('onclick', 'return false');
            } else {
                row.find(':input').prop('readonly', true);
            }

            if (data.type == 'arrayinput' || data.type == 'dictinput') {
                row.find('.fn-add, .fn-remove').remove();
            }
        }
        if (data.required)
            row.find(':input').filter('input:not([type=checkbox])').prop('required', true);
        if (data.placeholder)
            row.find(':input').attr('placeholder', data.placeholder);
        if (data.hidden)
            row.hide();

        // Extra processing
        var processor = processors[data.type];
        if (processor)
            processor(row, data);

        return row;
    };


    var defaultOptions = {
        style: 'aligned'  // or 'stacked'
    };


    var renderForm = function(el, schema, _options) {
        var options = {};
        $.extend(options, defaultOptions);
        $.extend(options, _options);
        // console.log('options', options);

        // Empty the element before append children
        el.empty();
        el.addClass('jsform');
        if (options.style == 'stacked') {
            el.addClass('jsform-stacked');
        }

        schema.forEach(function (i){
            var row = renderRow(i);
            el.append(row);
        });
    };


    var customTypes = {};


    var registerCustomType = function(name, options) {
        if (!('template' in options))
            throw '`template` must in options';
        templates[name] = Handlebars.compile(options.template);

        if (!('serializer' in options))
            throw '`serializer` must in options';
        serializers[name] = options.serializer.bind(options);

        if ('processor' in options)
            processors[name] = options.processor.bind(options);
    };


    var serializers = {};


    var serializeForm = function(el) {
        var data = {};

        el.find(".form-row").each(function(index, _row) {
            var row = $(_row),
                type = row.attr("data-type"),
                key = row.attr("data-key");
            // console.log('row', row, row.hasClass('form-row-disabled'));

            if (row.hasClass('form-row-disabled'))
                return;

            switch (type) {
                case "text":
                case "textarea":
                    var i = row.find(":input");
                    data[key] = i.val();
                    break;

                case "number":
                    var i = row.find("input"),
                        v = i.val();
                    data[key] = v ? Number(i.val()) : NaN;
                    break;

                case "checkbox":
                    var i = row.find("input");
                    data[key] = i.prop("checked");
                    break;

                case "select":
                    var i = row.find("option:selected");
                    data[key] = i.prop("value");
                    break;

                case "arrayinput":
                    var buf = [];
                    row.find(".input-group input").each(function(index, o){
                        var value = $(o).val();
                        if (value)
                            buf.push(value);
                    });
                    data[key] = buf;
                    break;

                case "dictinput":
                    var buf = {};
                    row.find(".input-group .dict-item").each(function(index, o){
                        var key = $(o).find('input[name="key"]').val(),
                            value = $(o).find('input[name="value"]').val();
                        // console.log(key + " " + value);
                        if (key)
                            buf[key] = value;
                    });
                    data[key] = buf;
                    break;

                case "multicheckbox":
                    var buf = {};
                    row.find('.input-group input[type="checkbox"]').each(function(index, o){
                        var key = $(o).attr("name"),
                            value = $(o).prop("checked");
                        buf[key] = value;
                    });
                    data[key] = buf;

                default:
                    serializer = serializers[type];
                    if (!serializer)
                        throw 'No relevant serializer for jsform type ' + type;
                    data[key] = serializer(row);
            }
        });

        return data;
    };


    var toJson = function(el) {
        return JSON.stringify(serializeForm(el));
    };

    var fillData = function(schema, data) {
        schema.forEach(function(i) {
            var value = data[i.key];
            if (i.type == 'dictinput') {
                i.items = [];
                for (var k in value) {
                    i.items.push({
                        key: k,
                        value: value[k]
                    });
                }
            } else {
                i.value = value;
            }
        });
    };

    // Export module
    var exports = {
        renderForm: renderForm,
        serializeForm: serializeForm,
        fillData: fillData,
        registerCustomType: registerCustomType,

        toJson: toJson,  // Keep the old
        toObject: serializeForm  // Keep the old
    };

    return exports;
});
