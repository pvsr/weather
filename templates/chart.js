var label = function(n) {
  return (t, i) => i % n === 0 ? (i === 0 ? 'Now' : t.toLocaleTimeString('en-US', { 'hour': 'numeric' })) : null;
};
var data = {
  labels: [{{ hourly | map(attribute='startTime') | map('quote') | join(',') }}]
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
          // TODO maybe derive from number of data points
          labelInterpolationFnc: label(6),
        }
      },
    ],
    ['screen and (min-width: 768px)',
      {
        axisX: {
          labelInterpolationFnc: label(3),
        }
      },
    ]
  ]
);
