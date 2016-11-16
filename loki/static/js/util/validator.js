define([
    'underscore',
    'sprintf'
], function(_, sprintf) {
    var exports = {};

    /*
    Schema = {
        name: {
            length: [5, 10]
        },
        age: {
            type: Number,
            range: [0, null]
        },
        height: {
            optional: true
        },
        gender: {
            choices: ['male', 'female']
        },
        has_girlfriend: {
            type: Boolean,
            custom: function(value) {
                // If you are a male and older than 20, and you don't have a gf,
                // it's not valid.
                if ((this.gender == 'male' && this.age > 20) && !value)
                    throw validator.Invalid('No gf is not allowed for man > 20!');
            }
        },
    }
    */
    var Schema = exports.Schema = function(schema, strict) {
        this.schema = schema;
        if (strict === undefined)
            strict = false;
        this.strict = strict;
    };

    _.extend(Schema.prototype, {
        validate: function(data) {
            var keys = Object.keys(this.schema),
                data_keys = Object.keys(data),
                errors = [],
                key, field, value;

            // check keys
            if (this.strict) {
                // When strict is true, data cannot have extra keys
                data_keys.forEach(function(i) {
                    if (_.contains(keys, i))
                        errors.push(new Invalid('key %s is not one of %s', i, keys));
                });
            }

            // check each field
            try {
                for (key in this.schema) {
                    // Only check for keys in schema
                    if (!this.schema.hasOwnProperty(key)) continue;

                    field = this.schema[key];
                    field.key = key;
                    value = data[key];

                    // constraint: optional (by default every key is required, means optional == false)
                    if (!_.has(field, 'optional'))
                        field.optional = false;
                    if (!_.has(data, key) && !field.optional)
                        throw new Invalid('key %s is required', key);

                    // constraint: type
                    if (field.hasOwnProperty('type'))
                        this.check_type(field, value);

                    // constraint: length
                    if (field.hasOwnProperty('length'))
                        this.check_length(field, value);

                    // constraint: range
                    if (field.hasOwnProperty('range'))
                        this.check_range(field, value);

                    // constraint: choices
                    if (field.hasOwnProperty('choices'))
                        this.check_choices(field, value);

                    // constraint: custom
                    if (field.hasOwnProperty('custom'))
                        this.check_custom(field, value);
                }
            } catch(e) {
                if (e instanceof Invalid) {
                    if (field.hasOwnProperty('message')) {
                        e.message = field.message + ' (' + e.message + ')';
                    }
                    errors.push(e);
                } else {
                    console.log(e);
                    console.log(e.stack);
                    throw e;
                }
            }

            return errors;
        },

        check_type: function(field, value) {
            if (!istypeof(value, field.type))
                throw new Invalid('%s should be of type %s', field.type);
        },
        check_length: function(field, value) {
            if (istypeof(field.length, Array)) {
                var min = field.length[0],
                    max = field.length[1];
                if (max === undefined)
                    max = null;
                // if (!(min <= value.length <= max))
                if (value < min || (max !== null && value > max))
                    throw new Invalid('%s length should be in range %s ~ %s',
                        field.key, min || '-∞', max || '∞');
            } else {
                if (field.length !== value.length)
                    throw new Invalid('%s length should be of %s', field.key, field.length);
            }
        },
        check_range: function(field, value) {
            if (!istypeof(value, Number))
                return;
            var min = field.range[0],
                max = field.range[1];
            if (!(min <= value <= max))
                throw new Invalid('%s should be of range %s', field.key, field.range);
        },
        check_choices: function(field, value) {
            if (!_.contains(field.choices, value))
                throw new Invalid('%s should be one of %s', field.key, field.choices);
        },
        check_custom: function(field, value, data) {
            /*
            Custom function indicate invalid when:
            1. it returns false
            2. it returns string
            3. it throws exception
            */
            var rv = field.custom.call(data, value);
            if (rv === false) {
                throw new Invalid('%s is invalid in custom check', field.key);
            } else if (istypeof(rv, String)) {
                throw new Invalid('%s is invalid in custom check: %s', field.key, rv);
            }
        }
    });

    var Invalid = exports.Invalid = function() {
            this.message = sprintf.sprintf.apply(this, arguments);
        },

        istypeof = function(value, type) {
            switch (type) {
                case String:
                    if (typeof value === 'string')
                        return true;
                    return false;
                case Number:
                    if (typeof value === 'number')
                        return true;
                    return false;
                case Boolean:
                    if (typeof value === 'boolean')
                        return true;
                    return false;
                case Array:
                    if (Array.isArray(value))
                        return true;
                    return false;
                case Object:
                    if (typeof value === 'object' && !Array.isArray(value) && value !== null)
                        return true;
                    return false;
                default:
                    console.warn('type not supported:', type);
                    return false;
            }
        };

    return exports;
});