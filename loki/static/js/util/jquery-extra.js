define([
    'jquery'
], function($) {
    /* Extend direct to use functions */
    $.extend({
        // Then absolute when, works no matter deferrs are success or not.
        absoluteWhen: function( subordinate /* , ..., subordinateN */ ) {
            var i = 0,
                slice = [].slice,
                resolveValues = slice.call( arguments ),
                length = resolveValues.length,

                // the count of uncompleted subordinates
                remaining = length !== 1 || ( subordinate && jQuery.isFunction( subordinate.promise ) ) ? length : 0,

                // the master Deferred
                deferred = jQuery.Deferred(),

                // Update function for both resolve and progress values
                updateFunc = function( i, contexts, values ) {
                    return function( value ) {
                        contexts[ i ] = this;
                        values[ i ] = arguments.length > 1 ? slice.call( arguments ) : value;
                        if ( values === progressValues ) {
                            deferred.notifyWith( contexts, values );
                        } else if ( !( --remaining ) ) {
                            console.log('resolveWith', contexts, values);
                            deferred.resolveWith( contexts, values );
                        }
                    };
                },

                progressValues = new Array( length ),
                progressContexts = new Array( length ),
                resolveContexts = new Array( length );

            // add listeners to Deferred subordinates; treat others as resolved
            for ( ; i < length; i++ ) {
                if ( resolveValues[ i ] && jQuery.isFunction( resolveValues[ i ].promise ) ) {
                    resolveValues[ i ].promise()
                        .done( updateFunc( i, resolveContexts, resolveValues ) )
                        //.fail( deferred.reject )
                        .fail( updateFunc( i, resolveContexts, resolveValues ) )
                        .progress( updateFunc( i, progressContexts, progressValues ) );
                } else {
                    --remaining;
                }
            }

            // if we're not waiting on anything, resolve the master
            if ( !remaining ) {
                deferred.resolveWith( resolveContexts, resolveValues );
            }

            return deferred.promise();
        },

        getxhr: function(args) {
            // success
            if (args[2].promise && jQuery.isFunction(args[2].promise)) {
                return args[2];
            // error
            } else if (args[0].promise && jQuery.isFunction(args[0].promise)) {
                return args[0];
            } else {
                console.error('Could not get xhr object', args);
            }
        },

        // Like $.extend, but more honest, never ignore undefined or null value keys in object
        honest_extend: function(obj) {
            var length = arguments.length;
            if (length < 2 || obj === null) return obj;
            for (var index = 1; index < length; index++) {
                var source = arguments[index],
                    type = typeof source,
                    is_object = type === 'function' || type === 'object' && !!source,
                    keys = [];

                if (!is_object) return keys;

                for (var _key in source) keys.push(_key);

                for (var i = 0; i < keys.length; i++) {
                    var key = keys[i];
                    obj[key] = source[key];
                }
            }
            return obj;
        }
    });


    /* Extend DOM functions */
    $.fn.extend({
        // Disable/enable button
        disable: function(flag) {
            if (flag === false) {
                // Enable
                this.prop('disabled', false);
            } else {
                this.prop('disabled', true);
            }
        },

        loading: function(flag) {
            var el = this;
            if (flag === false) {
                // Hide loader
            } else {
                // Show loader
                var loader = $('<div class="overlay-loader"></div>');
                console.log('loader', loader, el);
                el.css('position', 'relative');
                el.append(loader);
                return loader;
            }
        }
    });
});
