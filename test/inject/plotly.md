---
title: Plotting with PlotLy
author: Johan Hidding
version: 1.0.0
footer: "Literate Programming made easy by [Entangled](https://entangled.github.io)!"
license:  "[Apache 2](https://www.apache.org/licenses/LICENSE-2.0)"
header-includes: >
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
---

# Plotting
Suppose we want to add some visualisations to our document? [PlotLy](https://plotly.com) is an extensive library with lots of options and examples. One of their examples shows how to make 3D surface plots. PlotLy loads a CSV file giving the result to a call-back function, putting the data in `rows`

The following snippet unpacks the data from `rows` and puts it in a format that PlotLy understands:

``` {.js #unpack-data}
function unpack(rows, key) {
  return rows.map(function(row) { return row[key]; });
}
  
var z_data=[ ]
for(i=0;i<24;i++)
{
  z_data.push(unpack(rows,i));
}
```

We can now define the data set:

``` {.js #define-plot-data}
var data = [{
           z: z_data,
           type: 'surface'
        }];
```

And have a suitable layout:

``` {.js #define-plot-layout}
var layout = {
  title: 'Mt Bruno Elevation',
  autosize: true,
  height: 700,
  margin: {
    l: 65,
    r: 50,
    b: 65,
    t: 90,
  }
};
```

The final plot command is given the `inject=` attribute, showing the result and the plotting boilerplate in a tabbed item.

``` {.js #myPlot inject=}
Plotly.d3.csv('https://raw.githubusercontent.com/plotly/datasets/'
             +'master/api_docs/mt_bruno_elevation.csv', function(err, rows){

<<unpack-data>>
<<define-plot-data>>
<<define-plot-layout>>

Plotly.newPlot('myPlot', data, layout);
});
```

This functionality could be extended to other languages that compile to Javascript.
