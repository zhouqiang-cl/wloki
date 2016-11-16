define([
    'underscore',
], function(_) {
    var log = console.log.bind(console);

    var oop = {};

    var class_extend = oop.class_extend = function(proto_props, static_props) {
        var parent = this,
            child;

        // The constructor function for the new subclass is either defined by you
        // (the "constructor" property in your `extend` definition), or defaulted
        // by us to simply call the parent's constructor.
        log('!proto_props', proto_props, proto_props.constructor);
        if (proto_props && _.has(proto_props, 'constructor')) {
            log('!proto_props has constructor');
            child = proto_props.constructor;
        } else {
            log('!define parent.apply');
            child = function() {
                return parent.apply(this, arguments);
            };
        }

        // Set the prototype chain to inherit from `parent`, without calling
        // `parent`'s constructor function.
        if (Object.create) {
            log('!use Object.create');
            child.prototype = Object.create(parent.prototype);
            child.prototype.constructor = child;
        } else {
            var NewProto = function() {
                this.constructor = child;
            };
            NewProto.prototype = parent.prototype;
            child.prototype = new NewProto();
        }

        // Add prototype properties (instance properties) to the subclass,
        // if supplied.
        if (proto_props) _.extend(child.prototype, proto_props);

        // Set a convenience property in case the parent's prototype is needed later.
        child.prototype.__super__ = parent.prototype;

        // Add static properties to the constructor function
        _.extend(child, parent, static_props);

        return child;
    };

    return oop;
});