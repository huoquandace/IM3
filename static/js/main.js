
// preview image before save
const IMAGE_SIZE = 150
$('#image').width(IMAGE_SIZE).height(IMAGE_SIZE)
$('#id_image').on('change', function(e) {
    if (e.target.files.length) {
        const src = URL.createObjectURL(e.target.files[0]);
        $('#image').attr('src', src).width(IMAGE_SIZE).height(IMAGE_SIZE).show();
    }
})