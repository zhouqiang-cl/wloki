require([
    'jquery',
    'loki',
    'contents',
    // 'jquery-toc'
], function($, loki, contents) {
    console.log('contents', contents);
    loki.configure({
        sidebar: null
    });

    loki.ready(function() {
        contents.contents({
            articles: $('#main').find('h1, h2, h3, h4, h5').get(),
            contents: $('#sidebar')[0]
        }).eventProxy.on('change', function(data) {
            if (data.previous) {
                $(data.previous.guide)
                    .removeClass('active')
                    .parents('li')
                    .removeClass('active-child');
            }

            $(data.current.guide)
                .addClass('active')
                .parents('li')
                .addClass('active-child');
        });
    });

    loki.run();
});
