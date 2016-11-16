// load the entire module/library and pass to the test
define([
    'util/oop',
    'underscore'
], function(oop, _) {

    var Base = window.Base = function(name, money) {
        console.log('Base');
        this.name = name;

        this.initialize();
    };
    Base.extend = oop.class_extend;
    _.extend(Base.prototype, {
        money: 10,
        initialize: function() {
            console.log('Base init');
        },
        hello: function() {
            return this.name;
        }
    });


    // use jasmine to run tests against the required code
    describe('Base class define:', function() {

        b_name = 'alice';
        b = new Base(b_name);

        it('Base has no money', function() {
            expect(Base.money).toBe(undefined);
        });

        it('b has money', function() {
            expect(b.money).toBe(10);
        });

        it('b can say hello', function() {
            expect(b.hello()).toBe(b_name);
        });
    });


    var Inherited = window.Inherited = Base.extend({
        money: 5,
        initialize: function() {
            this.__super__.initialize.call(this);
            this.money = this.__super__.money + this.money;
        },
        hey: function() {
            var rv = this.__super__.hello.call(this);
            return rv + '!';
        }
    }, {
        get_this: function() {
            return this;
        }
    });

    describe('Inherited class define:', function() {
        i_name = 'anna';
        i = new Inherited(i_name);

        it('Inherited has no money', function() {
            expect(Inherited.money).toBe(undefined);
        });

        it('i has money', function() {
            expect(i.money).toBe(15);
        });

        it('i can also say hello', function() {
            expect(i.hello()).toBe(i_name);
        });

        it('i can say hey!', function() {
            expect(i.hey()).toBe(i_name + '!');
        });

        it('Inherited has static method', function() {
            expect(Inherited.get_this()).toBe(Inherited);
        });

        it('but i has no static method', function() {
            expect(i.get_this).toBe(undefined);
        });
    });
});

