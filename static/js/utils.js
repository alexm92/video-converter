var converted_ids = {};
var polling_setInterval;

function setUploadButtonWhenReady(){
    $(document).ready(function () {
        $('#fineuploader-s3').fineUploaderS3({
            retry: {
                enableAuto: true // defaults to false
            },

            request: {
                // REQUIRED: We are using a custom domain
                // for our S3 bucket, in this case.  You can
                // use any valid URL that points to your bucket.
                endpoint: "https://video-converter-s3.s3.amazonaws.com",

                // REQUIRED: The AWS public key for the client-side user
                // we provisioned.
                accessKey: "AKIAJLCP6ZNHGZYROVBA"
            },

            template: "simple-previews-template",

            // REQUIRED: Path to our local server where requests
            // can be signed.
            signature: {
                endpoint: "/upload/"
            },

            // OPTIONAL: An endopint for Fine Uploader to POST to
            // after the file has been successfully uploaded.
            // Server-side, we can declare this upload a failure
            // if something is wrong with the file.
            //uploadSuccess: {
            //    endpoint: "/s3demo.php?success"
            //},

            // USUALLY REQUIRED: Blank file on the same domain
            // as this page, for IE9 and older support.
            iframeSupport: {
                localBlankPagePath: "/blankIE9.html"
            },

            // optional feature
            chunking: {
                enabled: false
            },

            // optional feature
            resume: {
                enabled: true
            },

            // optional feature
            deleteFile: {
                enabled: true,
                method: "POST",
                endpoint: "/upload/"
            },

            // optional feature
            validation: {
                itemLimit: 1,
                sizeLimit: 2147483648,
                acceptFiles: "video/*",
                allowedExtensions: ["mp4", "avi", "mpeg", "mpg", "mkv", "mpeg", "png", "jpeg", "jpg", "bmp", "gif"]
            },

            thumbnails: {
                placeholders: {
                    notAvailablePath: "/static/img/not_available-generic.png",
                    waitingPath: "/static/img/waiting-generic.png"
                }
            }
        })
        // Enable the "view" link in the UI that allows the file to be downloaded/viewed
        .on('complete', function(event, id, name, response) {
            var $fileEl = $(this).fineUploaderS3("getItemByFileId", id),
                $viewBtn = $fileEl.find(".view-btn");

            if (response.success) {
                // show next tab
                $('.nav a:eq(1)').tab('show');

                $('.form-horizontal').show();
                $('.progress').hide();
                $('#btn_convert').show();

                // add to SQS and start converting
                $('#btn_convert').click(function () {
                    if (typeof(converted_ids[id]) == "undefined"){
                        converted_ids[id] = true;
                        startConverting(response);
                    }
                });
            }
        });
    });
}

function startConverting(response) {
    $.ajax({
        url: '/api/convert/',
        data: {
            path: response.tempLink, 
            width: $('#txt_width').val(), 
            height: $('#txt_height').val(),
            gray: $('#ck_grayscale').is(':checked')
        },
        success: function () {
            $('.form-horizontal').hide();
            $('.progress').show();
            $('#btn_convert').hide();
            startPollingForProgress(response.tempLink);
        },
        error: function () {
            alert('error')
        }
    });
}

function download(filename) {
    $('.nav a:eq(2)').tab('show');
    $('#convert-bar').css('width', '0%');
    $('.sr-only').html('0% Complete (convert)');
    $.ajax({
        url: '/api/get_url/',
        data: {path: filename},
        success: function (data) {
             $('#btn_download').attr('href', data['url']);
        },
        error: function () {
            alert('download error');
        }
    });
}

function startPollingForProgress(ajax_url){
    var seconds = 1;
    polling_setInterval = setInterval(function(){
        $.ajax({
            url: '/api/progress',
            data: {'path' : ajax_url},
            success: function(data) {
                if (data['progress'] == '100'){
                    clearInterval(polling_setInterval);
                    download(ajax_url);
                }
                if (data['progress'] == '-1'){
                    clearInterval(polling_setInterval);
                    $('.nav a:eq(0)').tab('show');
                    alert("There was a problem with your file. Please try a different one.");
                    data['progress'] = '0';    
                }
                $('#convert-bar').css('width', data['progress'] + '%');
                $('.sr-only').html(data['progress'] + '% Complete (convert)');

            },
            error: function () {
                alert('progress error');
                clearInterval(polling_setInterval);
            }
        })
    }, 1 * 1000);
}
