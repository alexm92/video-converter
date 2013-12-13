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
                itemLimit: 5,
                sizeLimit: 2147483648
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
                    $viewBtn.show();
                    response.tempLink = $(this).fineUploaderS3('getKey', id);
                    console.log(this);
                    console.log($(this));
                    $viewBtn.attr("href", response.tempLink);

                    $.ajax({
                        url: '/api/convert/',
                        data: {path: response.tempLink},
                        beforeSend: function () { $('.nav a:eq(1)').tab('show'); },
                        success: function () {
                            $('.nav a:eq(2)').tab('show');
                        },
                        error: function () {
                            alert('error')
                        }
                    });
                }
            });
    });
}
