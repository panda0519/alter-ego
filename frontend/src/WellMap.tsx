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

function fieldRing(wells: Well[]): L.LatLngExpression[] {
  const points = wells.map(well => ({ x: well.longitude, y: well.latitude }))
    .sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (o: { x: number; y: number }, a: { x: number; y: number }, b: { x: number; y: number }) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const build = (source: typeof points) => {
    const ring: typeof points = [];
    for (const point of source) {
      while (ring.length >= 2 && cross(ring[ring.length - 2], ring[ring.length - 1], point) <= 0) ring.pop();
      ring.push(point);
    }
    return ring;
  };
  const lower = build(points);
  const upper = build([...points].reverse());
  lower.pop();
  upper.pop();
  return [...lower, ...upper].map(point => [point.y, point.x]);
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

      const ring = fieldRing(locatedWells);
      if (ring.length >= 3) {
        L.polygon(ring, {
          color: '#0F8D85', weight: 2, dashArray: '7 6', fillColor: '#3CCBC0', fillOpacity: 0.12, interactive: false,
        }).addTo(map);
      }

      for (const well of locatedWells) {
        const marker = L.marker([well.latitude, well.longitude], { icon: wellIcon(), keyboard: false }).addTo(map);
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
    <p className="region-label">Demonstration region. Positions are the exported coordinates for this dataset.</p>
    <p id="map-help">Select a well marker or use the station list. Focus a marker and press Enter or Space. The larger aqua marker is selected.</p>
    <p className="region-label">The outline groups the exported station coordinates. Teal is normal priority. Amber is watch or high. This is not a surveyed field boundary.</p>
    {locatedWells.length !== wells.length && <p role="status">{wells.length - locatedWells.length} well locations cannot be mapped. Their list entries remain available.</p>}
    {!locatedWells.length && <p className="notice" role="status">No valid well coordinates are available. Use the well list and details.</p>}
    {!!locatedWells.length && <>
      <div ref={container} className="well-map" role="region" aria-label="Well locations" aria-describedby="map-help" />
      <p role="status" className="map-status">{status === 'loading' ? 'Loading map tiles...' : status === 'ready' ? 'Map tiles loaded.' : status === 'tiles-unavailable' ? 'Background map tiles are unavailable or incomplete. Well markers, the list and details remain usable.' : 'The map could not be initialized. Use the well list and details.'}</p>
      {status === 'tiles-unavailable' && <button type="button" onClick={() => retryTiles.current?.()}>Retry map tiles</button>}
    </>}
  </section>;
}
