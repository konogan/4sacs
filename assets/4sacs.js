function replaceGeoBlocksWithMaps() {
    document.querySelectorAll("pre.geo").forEach((pre, index) => {
        const lat = parseFloat(pre.dataset.lat);
        const lng = parseFloat(pre.dataset.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        const mapDiv = document.createElement("div");
        mapDiv.id = `leaflet-map-${index}`;
        mapDiv.style.width = "100%";
        mapDiv.style.height = "300px";
        mapDiv.style.margin = "1em 0";

        pre.replaceWith(mapDiv);

        const map = L.map(mapDiv, {
            fullscreenControl: true,
            fullscreenControlOptions: {position: "topleft"},
        }).setView([lat, lng], 13);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
        }).addTo(map);

        L.marker([lat, lng]).addTo(map).bindPopup(
            `Latitude: ${lat}<br>Longitude: ${lng}`
        );

        map.on("fullscreenchange", () => setTimeout(() => map.invalidateSize(), 300));
    });
}

function initCategoryMap() {
    const items = document.querySelectorAll("li.category[data-lat][data-lng]");
    if (items.length === 0) return;

    let mapContainer = document.getElementById("map");
    if (!mapContainer) {
        const listParent = items[0].closest("ul") || document.body;
        mapContainer = document.createElement("div");
        mapContainer.id = "map";
        mapContainer.classList.add("category-map");
        mapContainer.setAttribute("role", "region");
        mapContainer.setAttribute("aria-label", "Carte des emplacements");
        listParent.before(mapContainer);
    }

    const map = L.map(mapContainer).setView([46.8, 2.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap",
    }).addTo(map);

    const markers = [];
    items.forEach((it) => {
        const lat = parseFloat(it.dataset.lat);
        const lng = parseFloat(it.dataset.lng);
        if (isNaN(lat) || isNaN(lng)) return;

        const title = it.querySelector("a")?.textContent || "(Sans titre)";
        const marker = L.marker([lat, lng]).addTo(map).bindPopup(`<b>${title}</b>`);
        markers.push({el: it, marker});
    });

    if (markers.length > 0) {
        const group = L.featureGroup(markers.map((m) => m.marker));
        map.fitBounds(group.getBounds().pad(0.2));
    }

    markers.forEach(({el, marker}) => {
        el.addEventListener("click", () => {
            map.setView(marker.getLatLng(), 14);
            marker.openPopup();
        });
    });
}


function highlightTimesInContent() {
    const containers = document.querySelectorAll('.content');
    if (containers.length === 0) return;

    const timePattern = /\b(\d{1,2}h(?:\d{2})?)\b/g;

    containers.forEach(container => {
        container.querySelectorAll('*').forEach(el => {
            el.childNodes.forEach(node => {
                if (node.nodeType === Node.TEXT_NODE && timePattern.test(node.textContent)) {
                    const newHTML = node.textContent.replace(timePattern, '<strong>$1</strong>');
                    const wrapper = document.createElement('span');
                    wrapper.innerHTML = newHTML;
                    node.replaceWith(...wrapper.childNodes);
                }
            });
        });
    });
}


highlightTimesInContent();
replaceGeoBlocksWithMaps();
initCategoryMap();
