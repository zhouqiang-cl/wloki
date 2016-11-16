var get_require_modules = function(base_dir) {
    var fs = require('fs'),
        _files = fs.readdirSync(base_dir),
        files;

     files = _files.filter(function(i) {
        if (fs.statSync(base_dir + '/' + i).isDirectory())
            return false;
        return !(/^\.|^require|^loki/).test(i);
    });

    modules = files.map(function(i) {
        return {name: i.split('.')[0]};
    });
    console.log(modules);
    return modules;
};


module.exports = function(grunt) {

    require('load-grunt-tasks')(grunt);

    var pkg = grunt.file.readJSON('package.json'),
        appConfig = {
            name: pkg.name,
            apps: [
                '',
            ],
        },
        require_modules = get_require_modules(pkg.name + '/static/js');

    // Project configuration.
    grunt.initConfig({
        app: appConfig,
        srcDir: '<%= app.name %>',
        destDir: '_build',
        tempDir: '.tmp',
        copy: {
            // Copy static/css/ to temp dir for further operation by usemin
            temp: {
                files: [
                    {
                        expand: true,
                        cwd: '<%= srcDir %>',
                        src: [
                            'static/css/**',
                        ],
                        dest: '<%= tempDir %>'
                    }
                ]
            },
            // Copy dirs and files no need for transformation directly to build
            build: {
                files: [
                    {
                        expand: true,
                        cwd: '<%= srcDir %>',
                        src: [
                            'static/img/**',
                            'static/css/fonts/**',
                            'template/**',
                        ],
                        dest: '<%= destDir %>'
                    }
                ]
            },
        },
        requirejs: {
            options: {
                appDir: '<%= srcDir %>/static/js',
                baseUrl: './',
                optimize: 'none',
                mainConfigFile: '<%= srcDir %>/static/js/require-config.js',
            },
            build: {
                options: {
                    dir: '<%= tempDir %>/static/js',
                    modules: require_modules
                }
            },
        },
        useminPrepare: {
            html: ['<%= srcDir %>/template/**/*.html'],
            options: {
                root: '<%= tempDir %>',  // root for resolving js and css files to transform
                dest: '<%= destDir %>',
                staging: '<%= tempDir %>'
            }
        },
        usemin: {
            html: '<%= destDir %>/template/{,*/}*.html',
            options: {
                assetsDirs: ['<%= destDir %>']
            }
        },
        uglify: {
            options: {
                preserveComments: false,
                mangle: false,
                compress: false,
                banner: '/*! Build by grunt in <%= grunt.template.today("yyyy-mm-dd") %> */\n'
            }
        },
        filerev: {
            options: {
              encoding: 'utf8',
              algorithm: 'md5',
              length: 8,
            },
            build: {
                src: [
                    '<%= destDir %>/**/*.js',
                    '<%= destDir %>/**/*.css',
                ]
            }
        },
        shell: {
            clean: {
                command: 'rm -rf <%= destDir %> <%= tempDir %>'
            },
            show_built: {
                command: 'tree <%= destDir %> -h'
            }
        }
    });

    grunt.registerTask('clean', ['shell:clean']);

    grunt.registerTask('build', [
        'clean',
        'copy',
        'useminPrepare',
        'requirejs',
        'concat',  // Called by usemin
        'uglify',  // Called by usemin
        'cssmin',  // Called by usemin
        'filerev',
        'usemin',
        'shell:show_built'
    ]);
};

