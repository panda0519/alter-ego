import { useEffect, useMemo, useRef, useState } from 'react';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Method, Well } from './data/models';
import { validCoordinates } from './data/coordinates';
import { priorityLabel } from './data/presentation';

interface Props { wells: Well[]; selectedId?: string; method?: Method; onSelect: (id: string) => void; active?: boolean }

function tooltipLabel(well: Well, method?: Method): string {
  const summary = method ? well.summaries?.[method] : undefined;
  const station = `${well.id} (${well.role})`;
  return summary ? `${station} · ${priorityLabel(summary.priority)}` : station;
}

function wellIcon(): L.DivIcon {
  return L.divIcon({
    className: 'well-marker',
    html: '<span class="well-head"></span>',
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function displayLatLng(wells: Well[]): Map<string, [number, number]> {
  const points = wells.map(well => {
    let hash = 2166136261;
    for (const char of well.id) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
    const unit = (shift: number) => ((Math.imul(hash ^ shift, 2246822519) >>> 0) % 10000) / 10000;
    return {
      id: well.id,
      lat: well.latitude + (unit(17) - 0.5) * 0.034,
      lon: well.longitude + (unit(53) - 0.5) * 0.038,
    };
  });
  const gap = 0.02;
  for (let pass = 0; pass < 12; pass += 1) {
    for (let i = 0; i < points.length; i += 1) {
      for (let j = i + 1; j < points.length; j += 1) {
        const left = points[i];
        const right = points[j];
        let dLat = right.lat - left.lat;
        let dLon = right.lon - left.lon;
        let dist = Math.hypot(dLat, dLon);
        if (dist === 0) { dLat = 0.001; dLon = 0.001; dist = Math.hypot(dLat, dLon); }
        if (dist >= gap) continue;
        const scale = ((gap - dist) / 2) / dist;
        left.lat -= dLat * scale;
        left.lon -= dLon * scale;
        right.lat += dLat * scale;
        right.lon += dLon * scale;
      }
    }
  }
  return new Map(points.map(point => [point.id, [point.lat, point.lon]]));
}
type MapStatus = 'loading' | 'ready' | 'tiles-unavailable' | 'map-unavailable';

export default function WellMap({ wells, selectedId, method, onSelect, active = true }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markers = useRef(new Map<string, L.Marker>());
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
      const placed = displayLatLng(locatedWells);
      const bounds = L.latLngBounds(locatedWells.map(well => L.latLng(...(placed.get(well.id) ?? [well.latitude, well.longitude]))));
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
        const [lat, lon] = placed.get(well.id) ?? [well.latitude, well.longitude];
        const marker = L.marker([lat, lon], { icon: wellIcon(), keyboard: false }).addTo(map);
        marker.bindTooltip(tooltipLabel(well, method));
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
      const element = marker.getElement();
      element?.classList.toggle('selected', selected);
      element?.setAttribute('aria-pressed', String(selected));
      marker.setZIndexOffset(selected ? 1000 : 0);
      if (selected && !mapRef.current?.getBounds().contains(marker.getLatLng())) mapRef.current?.panTo(marker.getLatLng(), { animate: false });
    }
  }, [selectedId, locatedWells, onSelect]);

  useEffect(() => {
    for (const well of locatedWells) {
      const marker = markers.current.get(well.id);
      const label = tooltipLabel(well, method);
      const priority = method ? well.summaries?.[method]?.priority : undefined;
      marker?.setTooltipContent(label);
      const element = marker?.getElement();
      element?.classList.toggle('watch', priority === 'watch' || priority === 'high');
      element?.setAttribute('aria-label', `Select well ${well.id} (${well.role})`);
    }
  }, [locatedWells, method]);

  useEffect(() => {
    if (active) mapRef.current?.invalidateSize({ pan: false });
  }, [active]);

  return <section className="panel map-panel" aria-labelledby="map-title">
    <h2 id="map-title">Station map</h2>
    <p className="region-label">Demonstration region. Markers are spaced unevenly for display. Distances on the map are not measurements.</p>
    <p id="map-help">Select a well marker or use the station list. Focus a marker and press Enter or Space. The larger aqua marker is selected.</p>
    <p className="region-label">Teal is normal priority. Amber is watch or high.</p>
    {locatedWells.length !== wells.length && <p role="status">{wells.length - locatedWells.length} well locations cannot be mapped. Their list entries remain available.</p>}
    {!locatedWells.length && <p className="notice" role="status">No valid well coordinates are available. Use the well list and details.</p>}
    {!!locatedWells.length && <>
      <div ref={container} className="well-map" role="region" aria-label="Well locations" aria-describedby="map-help" />
      <p role="status" className="map-status">{status === 'loading' ? 'Loading map tiles...' : status === 'ready' ? 'Map tiles loaded.' : status === 'tiles-unavailable' ? 'Background map tiles are unavailable or incomplete. Well markers, the list and details remain usable.' : 'The map could not be initialized. Use the well list and details.'}</p>
      {status === 'tiles-unavailable' && <button type="button" onClick={() => retryTiles.current?.()}>Retry map tiles</button>}
    </>}
  </section>;
}
