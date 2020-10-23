$(document).ready(function () {
    $('.lat-lon--widget').each(function () {
        var $parent = $(this);

        // Initialize the map
        var mapContainer = $parent.find('.lat-lon--map').get(0);
        var currentLat = $parent.find('input[type=number]:first').val()
        var currentLon = $parent.find('input[type=number]:last').val()
        var map = new mapboxgl.Map($.extend({
            container: mapContainer,
            style: 'mapbox://styles/mapbox/streets-v11',
            center: [currentLon, currentLat],
            zoom: 8
        }, $parent.data()));
        var nav = new mapboxgl.NavigationControl();
        map.addControl(nav);

        var marker = new mapboxgl.Marker()
            .setLngLat([currentLon, currentLat])
            .addTo(map);

        // React on raw value change
        $parent.find('input[type=number]').on('change keypress', function () {
            marker.setLngLat([
                parseFloat($parent.find('input[type=number]:last').val()),
                parseFloat($parent.find('input[type=number]:first').val())
            ])
            map.flyTo({
                center: marker.getLngLat()
            });
        })

        // React on click
        map.on('click', function (e) {
            marker.setLngLat(e.lngLat)
            $parent.find('input[type=number]:first').val(e.lngLat.lat.toFixed(6))
            $parent.find('input[type=number]:last').val(e.lngLat.lng.toFixed(6))
            map.flyTo({
                center: marker.getLngLat()
            });
        });

        // Add geocoding
        $parent.find('button.geocode').click(function () {
            var $form = $parent.parents('form');
            var prefix = $parent.find('input').attr('id').split('-').slice(0, -1).join('-');
            var search_parts = [
                $form.find('#' + prefix + '-street_number').val(),
                $form.find('#' + prefix + '-street').val(),
                $form.find('#' + prefix + '-postal_code').val(),
                $form.find('#' + prefix + '-city').val(),
                $form.find('#' + prefix + '-state').val(),
                $form.find('#' + prefix + '-country').val() && $form.find('#' + prefix + '-country option:selected').text()
            ];
            $.get('/geocoding', {
                q: search_parts.join(' ').trim().replace('  ', ' ')
            }, function (data) {
                var $container = $parent.find('.geocode-results');
                if (data.error) {
                    $container.text(data.error)
                } else {
                    var $list = $('<ol></ol>')
                    $.each(data.results, function (i, result) {
                        var tempMarker;
                        $('<li></li>')
                            .text(result.label)
                            .appendTo($list)
                            .hover(function () {
                                // Animate a grey marker to the location
                                tempMarker = new mapboxgl.Marker({color: 'grey'})
                                    .setLngLat([result.location.lng, result.location.lat])
                                    .addTo(map);
                                map.flyTo({
                                    speed: 4,
                                    center: tempMarker.getLngLat()
                                });
                            }, function () {
                                // Revert to previous location
                                tempMarker.remove()
                                map.flyTo({
                                    speed: 4,
                                    center: marker.getLngLat()
                                });
                            })
                            .click(function () {
                                marker.setLngLat([
                                    result.location.lng,
                                    result.location.lat
                                ])
                                $parent.find('input[type=number]:last').val(result.location.lng.toFixed(8))
                                $parent.find('input[type=number]:first').val(result.location.lat.toFixed(8))
                                map.flyTo({
                                    center: marker.getLngLat()
                                });
                            })
                    })
                    $container.html($list)
                }
            })
        })
    });
});
