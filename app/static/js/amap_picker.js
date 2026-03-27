/**
 * AmapPicker — 高德地图选点组件
 *
 * 使用方法：
 *   const picker = new AmapPicker('map-container-id', {
 *     onSelect : (lat, lng, address) => { ... },  // 选点回调（必填）
 *     defaultLat: 22.7,   // 初始纬度（可选）
 *     defaultLng: 114.3,  // 初始经度（可选）
 *     searchInputId: 'amap-search-input',  // 搜索框元素 id（可选）
 *   });
 *   picker.init();
 */
class AmapPicker {
  constructor(containerId, options = {}) {
    this.containerId   = containerId;
    this.onSelect      = options.onSelect     || function () {};
    this.defaultLat    = options.defaultLat   || 22.6899;
    this.defaultLng    = options.defaultLng   || 114.3490;
    this.searchInputId = options.searchInputId || 'amap-search-input';

    this.map        = null;
    this.marker     = null;
    this.geocoder   = null;
    this._resultBox = null;
  }

  init() {
    // 全局样式：确保自定义结果列表在 Bootstrap Modal 之上
    if (!document.getElementById('amap-picker-style')) {
      const style = document.createElement('style');
      style.id = 'amap-picker-style';
      style.textContent = `
        .amap-picker-results {
          position: absolute; left: 0; right: 0; top: 100%;
          background: #fff; border: 1.5px solid #e2e8f0;
          border-radius: 10px; box-shadow: 0 6px 20px rgba(0,0,0,0.12);
          max-height: 280px; overflow-y: auto; z-index: 99999;
          margin-top: 4px; display: none;
        }
        .amap-picker-results-item {
          padding: 10px 14px; cursor: pointer;
          border-bottom: 1px solid #f1f5f9; transition: background 0.15s;
        }
        .amap-picker-results-item:last-child { border-bottom: none; }
        .amap-picker-results-item:hover { background: #fffbeb; }
        .amap-picker-results-item .poi-name {
          font-size: 13px; font-weight: 600; color: #1e293b;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .amap-picker-results-item .poi-addr {
          font-size: 11px; color: #94a3b8; margin-top: 2px;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .amap-picker-results-item .poi-dist {
          flex-shrink: 0; font-size: 11px; font-weight: 700;
          color: #ff8800; margin-left: 10px; white-space: nowrap;
        }
        .amap-picker-results-empty {
          padding: 14px; text-align: center; color: #94a3b8; font-size: 13px;
        }
      `;
      document.head.appendChild(style);
    }

    // 地图实例
    this.map = new AMap.Map(this.containerId, {
      zoom    : 15,
      center  : [this.defaultLng, this.defaultLat],
      mapStyle: 'amap://styles/normal',
    });

    // 中心 Pin
    this.marker = new AMap.Marker({
      position : [this.defaultLng, this.defaultLat],
      draggable: true,
      cursor   : 'move',
      title    : '拖动调整位置',
    });
    this.map.add(this.marker);

    // 逆地理编码服务
    AMap.plugin('AMap.Geocoder', () => {
      this.geocoder = new AMap.Geocoder({ radius: 100 });
    });

    // 拖拽 marker 后更新地址
    this.marker.on('dragend', (e) => {
      const { lng, lat } = e.lnglat;
      this._reverseGeocode(lat, lng);
    });

    // 点击地图移动 marker
    this.map.on('click', (e) => {
      const { lng, lat } = e.lnglat;
      this.marker.setPosition([lng, lat]);
      this._reverseGeocode(lat, lng);
    });

    // 自定义搜索：PlaceSearch 按距离排序
    this._initCustomSearch();
  }

  /** 自定义搜索框：输入关键词 → PlaceSearch 附近搜索 → 按距离排序 */
  _initCustomSearch() {
    const inputEl = document.getElementById(this.searchInputId);
    if (!inputEl) return;

    // 结果列表挂在搜索框的父容器下
    const wrap = inputEl.closest('.input-group') || inputEl.parentElement;
    wrap.style.position = 'relative';

    const list = document.createElement('div');
    list.className = 'amap-picker-results';
    wrap.appendChild(list);
    this._resultBox = list;

    AMap.plugin(['AMap.PlaceSearch'], () => {
      const placeSearch = new AMap.PlaceSearch({ pageSize: 10 });
      let timer = null;

      inputEl.addEventListener('input', () => {
        clearTimeout(timer);
        const kw = inputEl.value.trim();
        if (!kw) { list.style.display = 'none'; return; }

        timer = setTimeout(() => {
          const center = this.map.getCenter();
          const cLng = typeof center.getLng === 'function' ? center.getLng() : center.lng;
          const cLat = typeof center.getLat === 'function' ? center.getLat() : center.lat;

          // 以地图中心为基准，50 km 内搜索，结果天然按距离排序
          placeSearch.searchNearBy(kw, [cLng, cLat], 50000, (status, result) => {
            list.innerHTML = '';
            if (status !== 'complete' || !result.poiList || !result.poiList.pois.length) {
              list.innerHTML = '<div class="amap-picker-results-empty">未找到相关地点</div>';
              list.style.display = 'block';
              return;
            }

            result.poiList.pois.forEach(poi => {
              const loc  = poi.location;
              const lng  = typeof loc.getLng === 'function' ? loc.getLng() : loc.lng;
              const lat  = typeof loc.getLat === 'function' ? loc.getLat() : loc.lat;
              const dist = poi.distance >= 1000
                ? (poi.distance / 1000).toFixed(1) + ' 千米'
                : Math.round(poi.distance) + ' 米';

              const item = document.createElement('div');
              item.className = 'amap-picker-results-item';
              item.innerHTML = `
                <div style="display:flex;align-items:center;">
                  <div style="flex:1;min-width:0;">
                    <div class="poi-name">${poi.name}</div>
                    <div class="poi-addr">${poi.address || ''}</div>
                  </div>
                  <div class="poi-dist">${dist}</div>
                </div>`;

              item.addEventListener('click', () => {
                this.map.setCenter([lng, lat]);
                this.marker.setPosition([lng, lat]);
                this._reverseGeocode(lat, lng);
                inputEl.value = poi.name;
                list.style.display = 'none';
              });

              list.appendChild(item);
            });

            list.style.display = 'block';
          });
        }, 400); // 400ms 防抖
      });

      // 点击搜索框外关闭列表
      document.addEventListener('click', (e) => {
        if (!wrap.contains(e.target)) list.style.display = 'none';
      });

      // ESC 关闭列表
      inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') list.style.display = 'none';
      });
    });
  }

  /** 自动定位到浏览器 GPS */
  autoLocate(onSuccess, onError) {
    AMap.plugin('AMap.Geolocation', () => {
      const geo = new AMap.Geolocation({
        enableHighAccuracy: true,
        timeout           : 8000,
        buttonPosition    : 'RB',
      });
      geo.getCurrentPosition((status, result) => {
        if (status === 'complete' && result.position) {
          const { lng, lat } = result.position;
          this.map.setCenter([lng, lat]);
          this.marker.setPosition([lng, lat]);
          this._reverseGeocode(lat, lng, onSuccess);
        } else {
          if (onError) onError(result);
        }
      });
    });
  }

  /** 强制设置坐标（外部调用） */
  setPosition(lat, lng) {
    this.map.setCenter([lng, lat]);
    this.marker.setPosition([lng, lat]);
    this._reverseGeocode(lat, lng);
  }

  _reverseGeocode(lat, lng, callback) {
    if (!this.geocoder) {
      setTimeout(() => this._reverseGeocode(lat, lng, callback), 300);
      return;
    }
    this.geocoder.getAddress([lng, lat], (status, result) => {
      let address = '';
      if (status === 'complete' && result.regeocode) {
        address = result.regeocode.formattedAddress;
      }
      this.onSelect(lat, lng, address);
      if (callback) callback(lat, lng, address);
    });
  }
}
