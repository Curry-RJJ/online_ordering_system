/**
 * 浏览器直传 COS：提交表单前先 PUT 到预签名 URL，再写入隐藏域并提交。
 * 依赖 base.html 中的 meta[name="csrf-token"]。
 */
(function () {
  var endpoint = '/upload/cos-presign';

  function getCsrf() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute('content') : '';
  }

  function presignPut(file, uploadType) {
    return fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf()
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        upload_type: uploadType,
        filename: file.name,
        content_type: file.type || 'application/octet-stream'
      })
    }).then(function (r) {
      return r.json();
    }).then(function (j) {
      if (j.code !== 200 || !j.data || !j.data.presigned_url) {
        throw new Error(j.message || '预签名失败');
      }
      return j.data;
    }).then(function (data) {
      return fetch(data.presigned_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': data.content_type },
        mode: 'cors'
      }).then(function (put) {
        if (!put.ok) {
          throw new Error('上传到 COS 失败 HTTP ' + put.status);
        }
        return data.web_path;
      });
    });
  }

  window.attachCosBrowserUpload = function (formSelector, fieldConfigs) {
    var form = document.querySelector(formSelector);
    if (!form || !form.getAttribute('data-cos-browser-upload')) {
      return;
    }
    form.addEventListener('submit', function (e) {
      if (form.getAttribute('data-require-map') === '1') {
        var latInp = document.getElementById('latitude');
        if (!latInp || !String(latInp.value).trim()) {
          e.preventDefault();
          alert('请先在地图上选点');
          return;
        }
      }
      var toUpload = [];
      for (var i = 0; i < fieldConfigs.length; i++) {
        var cfg = fieldConfigs[i];
        var inp = document.getElementById(cfg.fileInputId);
        var f = inp && inp.files && inp.files[0];
        if (f) {
          toUpload.push({ cfg: cfg, file: f, inp: inp });
        }
      }
      if (toUpload.length === 0) {
        return;
      }
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
      }
      var chain = Promise.resolve();
      toUpload.forEach(function (item) {
        chain = chain.then(function () {
          return presignPut(item.file, item.cfg.uploadType).then(function (path) {
            var hidden = form.querySelector('[name="' + item.cfg.hiddenName + '"]');
            if (hidden) {
              hidden.value = path;
            }
            item.inp.removeAttribute('name');
          });
        });
      });
      chain.then(function () {
        form.submit();
      }).catch(function (err) {
        alert(err.message || String(err));
        if (btn) {
          btn.disabled = false;
        }
      });
    });
  };
})();
