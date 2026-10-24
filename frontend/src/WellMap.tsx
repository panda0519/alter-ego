import { useEffect, useMemo, useRef, useState } from 'react';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Well } from './data/models';
import { validCoordinates } from './data/coordinates';

interface Props { wells: Well[]; selectedId?: string; onSelect: (id: string) => void }
type MapStatus = 'loading' | 'ready' | 'tiles-unavailable' | 'map-unavailable';

export default function WellMap({ wells, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markers = useRef(new Map<string, L.CircleMarker>());
  const retryTiles = useRef<(() => void) | null>(null);
  const [status, setStatus] = useState<MapStatus>('loading');
  const locatedWells = useMemo(() => wells.filter(well => validCoordinates(well.latitude, well.longitude)), [wells]);

  useEffect(() => {
    if (!container.current || !locatedWells.length) return;
    let map: L.Map | undefined;
    let tiles: L.TileLayer | undefined;
    let observer: ResizeObserver | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let disposed = false;
    const removeListeners: (() => void)[] = [];
    const cleanup = () => {
      disposed = true;
      clearTimeout(timer);
      observer?.disconnect();
      removeListeners.forEach(remove => remove());
      retryTiles.current = null;
      tiles?.off();
      markers.current.clear();
      map?.remove();
      map = undefined;
      mapRef.current = null;
    };
    try {
      setStatus('loading');
      map = L.map(container.current, { scrollWheelZoom: false });
      mapRef.current = map;
      const bounds = L.latLngBounds(locatedWells.map(well => L.latLng(well.latitude, well.longitude)));
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 12, animate: false });

      let failed = false;
      const startTimer = () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          if (!disposed) { failed = true; setStatus('tiles-unavailable'); }
        }, 10000);
      };
      tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      });
      tiles.on('tileerror', () => {
        if (!disposed) { failed = true; clearTimeout(timer); setStatus('tiles-unavailable'); }
      });
      tiles.on('load', () => {
        if (!disposed && !failed) { clearTimeout(timer); setStatus('ready'); }
      });
      tiles.on('loading', () => { if (!disposed && !failed) { setStatus('loading'); startTimer(); } });
      startTimer();
      tiles.addTo(map);
      retryTiles.current = () => { failed = false; setStatus('loading'); startTimer(); tiles?.redraw(); };

      for (const well of locatedWells) {
        const marker = L.circleMarker([well.latitude, well.longitude], {
          radius: 8, color: '#193b40', fillColor: '#438986', fillOpacity: 0.9, weight: 2,
        }).addTo(map);
        const tooltip = document.createElement('span');
        tooltip.textContent = `${well.id} (${well.role})`;
        marker.bindTooltip(tooltip);
        marker.on('click', () => onSelect(well.id));
        const element = marker.getElement();
        if (element) {
          element.setAttribute('role', 'button');
          element.setAttribute('tabindex', '0');
          element.setAttribute('aria-label', `Select well ${well.id} (${well.role})`);
          element.setAttribute('data-well-id', well.id);
          const keydown = (event: Event) => {
            const key = (event as KeyboardEvent).key;
            if (key === 'Enter' || key === ' ') {
              event.preventDefault(); event.stopPropagation(); onSelect(well.id);
            }
          };
          element.addEventListener('keydown', keydown);
          removeListeners.push(() => element.removeEventListener('keydown', keydown));
        }
        markers.current.set(well.id, marker);
      }
      observer = new ResizeObserver(() => { if (!disposed) map?.invalidateSize({ pan: false }); });
      observer.observe(container.current);
    } catch {
      cleanup();
      setStatus('map-unavailable');
    }
    return cleanup;
  }, [locatedWells, onSelect]);

  useEffect(() => {
    for (const [id, marker] of markers.current) {
      const selected = id === selectedId;
      marker.setStyle({ color: selected ? '#713209' : '#193b40', fillColor: selected ? '#f6b35b' : '#438986', weight: selected ? 4 : 2 });
      marker.setRadius(selected ? 11 : 8);
      marker.getElement()?.setAttribute('aria-pressed', String(selected));
      if (selected) {
        marker.bringToFront();
        if (!mapRef.current?.getBounds().contains(marker.getLatLng())) mapRef.current?.panTo(marker.getLatLng(), { animate: false });
      }
    }
  }, [selectedId, locatedWells, onSelect]);

  return <section className="panel map-panel" aria-labelledby="map-title">
    <p className="eyebrow">02 / Region</p>
    <h2 id="map-title">Well map</h2>
    <p id="map-help">Select a circle or use the well list. Focus a circle and press Enter or Space. The larger amber circle is selected.</p>
    {locatedWells.length !== wells.length && <p role="status">{wells.length - locatedWells.length} well locations cannot be mapped. Their list entries remain available.</p>}
    {!locatedWells.length && <p className="notice" role="status">No valid well coordinates are available. Use the well list and details.</p>}
    {!!locatedWells.length && <>
      <div ref={container} className="well-map" role="region" aria-label="Well locations" aria-describedby="map-help" />
      <p role="status" className="map-status">{status === 'loading' ? 'Loading map tiles...' : status === 'ready' ? 'Map tiles loaded.' : status === 'tiles-unavailable' ? 'Background map tiles are unavailable or incomplete. Well circles, the list and details remain usable.' : 'The map could not be initialized. Use the well list and details.'}</p>
      {status === 'tiles-unavailable' && <button type="button" onClick={() => retryTiles.current?.()}>Retry map tiles</button>}
    </>}
  </section>;
}
