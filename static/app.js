const form = document.getElementById('weather-form');
const placeInput = document.getElementById('place');
const resultEl = document.getElementById('result');
const errorEl = document.getElementById('error');

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove('hidden');
  resultEl.classList.add('hidden');
}

function showResult(data) {
  resultEl.innerHTML = `
    <strong>地点：</strong>${data.location}<br>
    <strong>天气：</strong>${data.weather_desc}（代码 ${data.weather_code}）<br>
    <strong>当前温度：</strong>${data.temperature} °C<br>
    <strong>今日温度：</strong>${data.today_min} °C ~ ${data.today_max} °C<br>
    <strong>湿度：</strong>${data.humidity}%<br>
    <strong>风速：</strong>${data.wind_speed} km/h<br>
    <strong>时区：</strong>${data.timezone}<br>
    <strong>坐标：</strong>${data.latitude}, ${data.longitude}<br>
    <strong>数据来源：</strong><a href="${data.source_url}" target="_blank" rel="noreferrer">${data.source}</a>
  `;
  resultEl.classList.remove('hidden');
  errorEl.classList.add('hidden');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const place = placeInput.value.trim();
  if (!place) {
    showError('请输入地理名称。');
    return;
  }

  try {
    const response = await fetch(`/api/weather?place=${encodeURIComponent(place)}`);
    const data = await response.json();

    if (!response.ok) {
      showError(data.error || '查询失败，请稍后重试。');
      return;
    }

    showResult(data);
  } catch {
    showError('网络异常，请检查连接后重试。');
  }
});
