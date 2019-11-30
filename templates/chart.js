var label = function(n) {
  return (t, i) => i % n === 0 ? (i === 0 ? 'Now' : t.toLocaleTimeString('en-US', { 'hour': 'numeric' })) : null;
};
var data = {
  labels: ['{{ hourly | join('\',\'', attribute='startTime') | safe }}']
  .map(tStr => new Date(tStr)),
  series: [[{{ hourly | join(',', attribute='fahrenheit') }}]]
};
new Chartist.Line('.ct-chart', data, {
  height: '200px', // TODO
  axisY: {
    labelInterpolationFnc: d => d + '°F',
  },
},
  [
    // TODO kind of arbitrary
    ['screen and (max-width: 768px)',
      {
        showPoint: false,
        axisX: {
          labelInterpolationFnc: label(4),
        }
      },
    ],
    ['screen and (min-width: 768px)',
      {
        axisX: {
          labelInterpolationFnc: label(2),
        }
      },
    ]
  ]
);
