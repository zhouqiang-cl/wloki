define([], function() {
    /* Change Array & String prototype */

    Array.prototype.contains = function(obj) {
        var i = this.length;
        while (i--) {
            if (this[i] === obj) {
                return true;
            }
        }
        return false;
    };

    if(typeof(String.prototype.strip) === "undefined") {
        String.prototype.strip = function() {
            return String(this).replace(/^\s+|\s+$/g, "");
        };
    }

});