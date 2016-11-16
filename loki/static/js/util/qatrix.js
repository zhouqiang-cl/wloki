/*
    Qatrix JavaScript v1.1.2

    Copyright (c) 2013, Angel Lai
    The Qatrix project is under MIT license.
    For details, see the Qatrix website: http://qatrix.com

    NOTE: This module contains only very small part of original Qatrix library,
    since most of Qatrix's functionality can be done by jQuery, using Qatrix
    should only for situations that need high performance DOM manipulating.

    Functions ported from Qatrix in this module are:

    $each
    $string (partly)
    $className
*/

(function (window, document, undefined) {

var
    /* BEGIN private vars and functions */
    version = '1.1.2',

    rspace = /\s+/,

    // For map function callback
    mapcall = function (match, callback)
    {
        if (match === null)
        {
            return;
        }

        if (callback === undefined)
        {
            return match;
        }

        var i = 0,
            length = match.length;

        if (length !== undefined && length > 0)
        {
            for (; i < length;)
            {
                if (callback.call(match[i], match[i], match[i++]) === false)
                {
                    break;
                }
            }

            return match;
        }
        else
        {
            return callback.call(match, match);
        }
    },
    /* END private vars and functions */


    /* BEGIN Qatrix module */

    Qatrix = {
    $: function (id)
    {
        return document.getElementById(id);
    },

    $each: function (haystack, callback)
    {
        var i = 0,
            length = haystack.length,
            type = typeof haystack,
            is_object = type === 'object',
            name;

        if (is_object && (length - 1) in haystack)
        {
            for (; i < length;)
            {
                if (callback.call(haystack[i], i, haystack[i++]) === false)
                {
                    break;
                }
            }
        }
        else if (is_object)
        {
            for (name in haystack)
            {
                callback.call(haystack[name], name, haystack[name]);
            }
        }
        else
        {
            callback.call(haystack, 0, haystack);
        }

        return haystack;
    },

    // $string contains `camelCase`, `replace`, `slashes`, `trim`, only `trim` is ported
    $string: {
        trim: "".trim ?
        function (string)
        {
            return string.trim();
        } :
        function (string)
        {
            return (string + '').replace(/^\s\s*/, '').replace(/\s\s*$/, '');
        }
    },

    $className: {
        add: function (elem, name)
        {
            return mapcall(elem, function (elem)
            {
                if (elem.className === '')
                {
                    elem.className = name;
                }
                else
                {
                    var ori = elem.className,
                        nclass = [];

                    Qatrix.$each(name.split(rspace), function (i, item)
                    {
                        if (!new RegExp('\\b(' + item + ')\\b').test(ori))
                        {
                            nclass.push(' ' + item);
                        }
                    });
                    elem.className += nclass.join('');
                }

                return elem;
            });
        },

        set: function (elem, name)
        {
            return mapcall(elem, function (elem)
            {
                elem.className = name;

                return elem;
            });
        },

        has: function (elem, name)
        {
            return new RegExp('\\b(' + name.split(rspace).join('|') + ')\\b').test(elem.className);
        },

        remove: function (elem, name)
        {
            return mapcall(elem, function (elem)
            {
                elem.className = name ? Qatrix.$string.trim(
                    elem.className.replace(
                        new RegExp('\\b(' + name.split(rspace).join('|') + ')\\b'), '')
                        .split(rspace)
                        .join(' ')
                ) : '';

                return elem;
            });
        }
    },

};
    /* END Qatrix module */


Qatrix.version = version;
window.Qatrix = Qatrix;

// Define Qatrix as an AMD module
if (typeof define === 'function' && define.amd)
{
    define([], Qatrix);
}

// Create a shortcut for compression
})(window, document);