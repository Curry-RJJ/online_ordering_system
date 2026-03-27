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
    this.defaultLat    = options.defaultLat   || 22.6899;   // 坪山区默认中心
    this.defaultLng    = options.defaultLng   || 114.3490;
    this.searchInputId = options.searchInputId || 'amap-search-input';

    this.map      = null;
    this.marker   = null;
    this.geocoder = null;
  }

  init() {
    // 修复：确保自动补全下拉框在 Bootstrap Modal 之上（z-index 问题）
    if (!document.getElementById('amap-picker-style')) {
      const style = document.createElement('style');
      style.id = 'amap-picker-style';
      style.textContent = '.amap-sug-result { z-index: 99999 !important; }';
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

    // 搜索框自动补全
    // 修复：按 v2.0 官方推荐，AutoComplete + PlaceSearch 组合使用。
    // v2.0 中 select 事件的 e.poi.location 可能为 null，需要 PlaceSearch 兜底查坐标。
    AMap.plugin(['AMap.AutoComplete', 'AMap.PlaceSearch'], () => {
      const auto = new AMap.AutoComplete({ input: this.searchInputId });
      const placeSearch = new AMap.PlaceSearch({ city: '全国', citylimit: false });

      auto.on('select', (e) => {
        if (!e.poi) return;

        // 优先使用 AutoComplete 直接返回的坐标
        const loc = e.poi.location;
        if (loc) {
          const lng = typeof loc.getLng === 'function' ? loc.getLng() : loc.lng;
          const lat = typeof loc.getLat === 'function' ? loc.getLat() : loc.lat;
          if (lng && lat) {
            this.map.setCenter([lng, lat]);
            this.marker.setPosition([lng, lat]);
            this._reverseGeocode(lat, lng);
            return;
          }
        }

        // location 为空时，用 PlaceSearch 按名称兜底获取坐标
        if (e.poi.name) {
          placeSearch.search(e.poi.name, (status, result) => {
            if (status === 'complete' &&
                result.poiList &&
                result.poiList.pois.length > 0) {
              const poi  = result.poiList.pois[0];
              const pLoc = poi.location;
              const lng  = typeof pLoc.getLng === 'function' ? pLoc.getLng() : pLoc.lng;
              const lat  = typeof pLoc.getLat === 'function' ? pLoc.getLat() : pLoc.lat;
              this.map.setCenter([lng, lat]);
              this.marker.setPosition([lng, lat]);
              this._reverseGeocode(lat, lng);
            }
          });
        }
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
      // geocoder 尚未加载完成，延迟重试
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
