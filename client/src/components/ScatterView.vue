<template>
    <div id="scatter-view">
        <div class="sliders">
            <div class="name">
                <p align="start"><b>Node Filter:&nbsp;</b>
                <input class="slider" type="range" min="0" :max="maxRelative" step=".001" v-model="lowerRange" @mouseup="drawChart"/>
                <b><span> ~&ensp;{{maxRelative}}</span><span style="color:#ff0000;">{{ lowerRange }}&ensp;</span></b>
                </p>
                <hr>
            </div>
        </div>
        <b-container class="scatter-view-container">
            <svg id="scatter">
            </svg>
        </b-container>
    </div>
</template>

<script>
    import * as d3 from "d3";
    import _ from "lodash";
    import {combinations} from '@/functionality/permutations'

    export default {
        name: "ScatterView",
        props: {
            relativeList: Array,
            items: Array,
            variableList: Array,
            N: Number,
            input: Array,
        },
        data() {
            return {
                Nn: null,
                title: "Relative View",
                lowerRange: 0,
                vlist: this.variableList,
                values: this.items,
                vrelatives: this.relativeList,
                vinput: this.input,
                nodes: [], // for bars up and down
                fullCircles: [],
                circles: [], // for scatters
                circlesUpdate: [],
                linksup: [],
                linksdown: [],
            }
        },

        watch: {
            lowerRange: function (oldValue, newValue) {
                this.fullCircles = [];
                let nn = this.vlist[0].flat();
                this.getCircles(nn);
                this.fullCircles.forEach(x => x.relative >= oldValue ? x.isvisible = true : x.isvisible = false)
                this.linksup = [];
                this.linksdown = [];
                this.glinks.selectAll('path').remove();
                this.gscatter.selectAll('circle').remove();
                this.gbarup.selectAll("rect").transition().remove().duration(1000);
                this.gbardown.selectAll("rect").transition().remove().duration(1000);
                this.gbarup.selectAll("text").transition().style("opacity", 1).remove().duration(1000);
                this.gbarup.selectAll("line").transition().style("opacity", 1).remove().duration(1000);
                this.gbarup.selectAll("path").transition().style("opacity", 1).remove().duration(1000);
                this.gbardown.selectAll("text").transition().style("opacity", 1).remove().duration(1000);
                this.gbardown.selectAll("line").transition().style("opacity", 1).remove().duration(1000);
                this.gbardown.selectAll("path").transition().style("opacity", 1).remove().duration(1000);
            },
            variableList: {
                immediate: true,
                handler() {
                    this.vlist = this.variableList;
                    this.Nn = this.variableList.length;
                }
            },
            relativeList: {
                immediate: true,
                handler() {
                    this.vrelatives = this.relativeList;
                }
            },
            items: {
                immediate: true,
                handler() {
                    this.values = this.items;

                    if (this.glinks) {
                        this.glinks.selectAll('path').remove();
                        this.gscatter.selectAll('circle').remove();
                        this.gbarup.selectAll("rect").remove();
                        this.gbardown.selectAll("rect").remove();
                        this.gbarup.selectAll("text").remove();
                        this.gbardown.selectAll("text").remove();

                        this.fullCircles = [];
                        this.nodes = [];
                        this.linksup = [];
                        this.linksdown = [];

                        let n = this.vlist[0].length;
                        if (this.vinput.length !==0) n = this.vinput.length;
                        this.getNodes(n);
                        let nn = this.vlist[0].flat();
                        this.getCircles(nn);

                        this.drawChart();
                    }

                }
            },

            input: {
                immediate: true,
                handler() {
                    this.vinput = this.input;
                }
            }
        },

        computed: {
            maxRelative: function() {
                return _.max(this.fullCircles.map(x => x.relative))
            },
        },

        mounted() {
            const body = document.body;
            const screenWidth = body.scrollWidth, screenHeight = body.scrollHeight;

            this.margins = {top: 5, bottom: 40, left: 60, right: 60};
            this.width = (screenWidth*3/12) - this.margins.left - this.margins.right;
            this.height = 610 - this.margins.top - this.margins.bottom;

            const y1 = d3.scaleLinear().range([90, 0]);
            const y2 = d3.scaleLinear().range([this.height - 90, this.height]);

            this.yAxisUp = d3.axisLeft()
                .scale(y1)
                .ticks(5)

            this.yAxisDown = d3.axisLeft()
                .scale(y2)
                .ticks(5);

            let svg = d3.select("svg#scatter")
                .attr("height", this.height + this.margins.top + this.margins.bottom)
                .attr("width", this.width + this.margins.left + this.margins.right);

            let gg = svg.append("g")
                .attr("transform", "translate(" + this.margins.left + "," + this.margins.top + ")");

            this.gbarup = gg.append('g')
                .attr('class', 'bars');

            this.gbardown = gg.append('g')
                .attr('class', 'bars');

            this.glinks = gg.append('g')
                .attr('class', 'links');

            this.gscatter = gg.append('g')
                .attr('class', 'scatter');

            this.drawChart();
        },

        methods: {
            getNodes(n) { // n = this.od only the first 4-order relations are plotted
                console.log(this.vlist)
                console.log(this.values, n)
                let acc_nodes = 0;
                for (let i = 0; i < n; i++) {
                    let order = i + 1;
                    let node = {};

                    for (let j = 0; j < this.vlist[i].length; j++) {
                        let v_name = this.vlist[i][j];
                        let sobol_value = this.values[i]['sobol'][j];
                        let sobol_total = this.values[i]['total'][j];
                        let relative_value = this.vrelatives[i][j];

                        node = {
                            "name": v_name.join("_"),
                            "sobol": sobol_value,
                            "total": sobol_total,
                            "relative": relative_value,
                            'grp': order,
                            "id": v_name.join("_"),
                            "active": false,
                            "clicked": false

                        };
                        if (i > 0 && j === 0) {
                            let order_len_pre = this.vlist[i - 1].length;
                            acc_nodes = acc_nodes + order_len_pre;
                        }
                        this.nodes[acc_nodes + j] = node;
                    }
                }
                console.log(this.nodes);
            },

            getCircles(n) {
                console.log(n)
                for (let i = 0; i < this.nodes.length; i++) {
                    let circle = {};
                    let currnode = this.nodes[i];
                    let currname = this.nodes[i]['name'].split("_").map(x => Number(x))

                    let rim_name = n;
                    for (let k = 0; k < currname.length; k++) {
                        let temp = _.without(rim_name, currname[k]);
                        rim_name = temp
                    }

                    let rim_subset = [];
                    for (let k = 0; k < rim_name.length; k++) { //0,1,2
                        let rim_set = combinations(rim_name, k + 1)
                        rim_subset.push(rim_set)
                    }

                    for (let j = 0; j < currnode['relative'].length; j++) { // [0,1,2,3,4]
                        let currelative = currnode['relative'][j]
                        for (let k = 0; k < currelative.length; k++) {
                            circle = {
                                "up_names": currnode.name,
                                "up_name": currnode.name.split("_").map(x => Number(x)),
                                "down_names": rim_subset[j][k].join("_"),
                                "down_name": rim_subset[j][k],
                                "relative": currelative[k],
                                'grp': currnode.grp,
                                'active': false,
                                'isvisible': true,
                                "clicked": false
                            };
                            this.fullCircles.push(circle)
                        }
                    }
                }
            },

            drawChart: function() {
                // ==============================================
                // ============== pre-drawing ===================
                // ==============================================
                let nodesBarUp = _.cloneDeep(this.nodes)
                    .filter((value, index, self) => {
                        return index < this.vlist[0].length
                    });
                let nodesBarDown = _.cloneDeep(this.nodes)
                    .filter((value, index, self) => {
                        return index < this.vlist[0].length
                    });

                let allNodes = nodesBarUp
                    .map(function (d) {
                        return d.name
                    });

                const color = ['#2ca8bd', '#28a744', '#a157a6', '#dc3445'];

                let resetu = 1;
                let resetd = 1;

                // A linear scale for bars size
                const size = d3.scaleLinear()
                    .domain([0, 1])
                    .range([0, 30]);

                // A linear scale to position the nodes on the X axis
                const x = d3.scalePoint()
                    .range([0, this.width])
                    .domain(allNodes);

                // use scale band for bar chart
                const xScale = d3.scaleBand()
                    .range([0, this.width])
                    .domain(allNodes)
                    .padding(.7)
                    .round(true);

                nodesBarUp.map(d => {
                    let xx = x(d.name) + xScale.bandwidth() / 2;
                    let yup = 90;
                    return d.xud = xx, d.yu = yup;
                })

                nodesBarDown.map(d => {
                    let xx = x(d.name) + xScale.bandwidth() / 2;
                    let ydown = this.height - 60;
                    return d.xud = xx, d.yd = ydown;
                })

                let tooltip1 = d3.select("body").append("div")
                    .attr("id", "tooltip1")
                    .style("position", "absolute")
                    .style("z-index", "10")
                    .style("visibility", "hidden");

                // ==============================================
                // ============   draw the bars   ===============
                // ==============================================

                let barup = this.gbarup.selectAll("bars-up")
                    .data(nodesBarUp)
                    .enter()
                    .append("rect")
                    .attr("x", function (d) {
                        return (x(d.name))
                    })
                    .attr("width", xScale.bandwidth())
                    .attr("y", function (d) {
                        return (90 - size(d.sobol) * 3)
                    })
                    .attr("height", function (d) {
                        return (size(d.sobol) * 3)
                    })
                    .style("fill", 'grey')
                    .style('opacity', 1)

                let barupforclick = this.gbarup.selectAll("bars-up")
                    .data(nodesBarUp)
                    .enter()
                    .append("rect")
                    .attr("x", function (d) {
                        return (x(d.name))
                    })
                    .attr("width", xScale.bandwidth())
                    .attr("y", function (d) {
                        return (90 - size(1) * 3)
                    })
                    .attr("height", function (d) {
                        return (size(1) * 3)
                    })
                    .style("fill", 'grey')
                    .style('opacity', 0)
                    .on('click', onClickBarUp)
                    .on('dblclick', dblClickBars);

                let barupx = this.gbarup.append('g')
                    .attr("class", "x axis")
                    .selectAll("text")
                    .data(nodesBarUp)
                    .enter()
                    .append("text")
                    .attr("x", function (d) {
                        return (x(d.name) + xScale.bandwidth()/2)
                    })
                    .attr("y", function (d) {
                        return 90 - size(d.sobol) * 3
                    })
                    .text(function (d) {
                        return (d.name)
                    })
                    .style("text-anchor", "start")
                    .attr("dx", "-.3em")
                    .attr("dy", "-.6em")
                    .style("font-size", 18)
                    .style("fill", 'grey');

                let self = this;
                let bardown = this.gbardown.selectAll("bars-down")
                    .data(nodesBarDown)
                    .enter()
                    .append("rect")
                    .attr("x", function (d) {
                        return (x(d.name))
                    })
                    .attr("width", xScale.bandwidth())
                    .attr("y", function (d) {
                        return (self.height - 60)
                    })
                    .attr("height", function (d) {
                        return (size(d.total) * 3)
                    })
                    .style("fill", 'grey')
                    .style('opacity', 1)

                let bardownforclick = this.gbardown.selectAll("bars-down")
                    .data(nodesBarDown)
                    .enter()
                    .append("rect")
                    .attr("x", function (d) {
                        return (x(d.name))
                    })
                    .attr("width", xScale.bandwidth())
                    .attr("y", function (d) {
                        return (self.height - 60)
                    })
                    .attr("height", function (d) {
                        return (size(1) * 3)
                    })
                    .style("fill", 'grey')
                    .style('opacity', 0)
                    .on('click', onClickBarDown)
                    .on('dblclick', dblClickBars);

                let bardownx = this.gbardown.append('g')
                    .attr("class", "x axis")
                    .selectAll("text")
                    .data(nodesBarDown)
                    .enter()
                    .append("text")
                    .attr("x", function (d) {
                        return (x(d.name) + xScale.bandwidth()/2)
                    })
                    .attr("y", function (d) {
                        return self.height - 35 + size(d.total) * 3
                    })
                    .text(function (d) {
                        return (d.name)
                    })
                    .style("text-anchor", "start")
                    .attr("dx", "-.3em")
                    .attr("dy", "-.2em")
                    .style("font-size", 18)
                    .style("fill", 'grey');

                let barupy = this.gbarup.append('g')
                    .attr("class", "y axis")
                    .call(this.yAxisUp)
                    .attr("transform", 'translate(-20,0)');
                
                let bardowny = this.gbardown.append('g')
                    .attr("class", "y axis")
                    .call(this.yAxisDown)
                    .attr("transform", 'translate(-20,30)')

                // ============================================
                //             draw the circles
                // ============================================

                let thisCircles = this.fullCircles
                let relativeRange = thisCircles.map(x => x.relative);
                let scaleCircleX = d3.scaleLinear()
                    .domain([0, _.max(relativeRange)])
                    .range([0, this.width]);

                let scaleCircleY = d3.scalePoint()
                    .domain(thisCircles.map(d => d.grp))
                    .range([180, this.height - 150]);

                // ====== try force layout bubble chart ======
                let circleSize = d3.scalePow()
                    .exponent(0.8)
                    .domain([0, _.max(relativeRange)])
                    .range([0.5, 8]);

                // construct the force layout bubble chart
                // force simulation creation, works like friction, adjusting the velocity of the nodes by multiplying by 1 - velocityDecay each tick.

                let simulation = d3.forceSimulation()
                    .force('x', d3.forceX().strength(0.05).x(this.width/2 + this.margins.left/4)) //
                    .force('y', d3.forceY().strength(1).y(function (d) {
                        return scaleCircleY(d.grp)
                    }))
                    .force("order-collide", d3.forceCollide(function (d) {
                        return circleSize(d.relative) + 0.1
                    }).iterations(5))
                    .nodes(thisCircles)
                    .on('tick', tick)
                    .stop();

                function tick() {
                    for (let i = 0; i < thisCircles.length; i++) {
                        let node = thisCircles[i];
                        node.cx = node.x;
                        node.cy = node.y;
                    }
                }

                // Run the layout a fixed number of times.
                // The ideal number of times scales with graph complexity.
                // Of course, don't run too long—you'll hang the page!
                const NUM_ITERATIONS = 100;
                simulation.tick(NUM_ITERATIONS);
                simulation.stop();

                // ============================================
                //             draw the links
                // ============================================

                let linkVertical = d3.linkVertical()
                    .x(function (d) {
                        return d.x;
                    })
                    .y(function (d) {
                        return d.y;
                    });

                let eachLinkUp = {}
                let eachLinkDown = {}
                for (let i = 0; i < thisCircles.length; i++) {
                    let nodeup = thisCircles[i].up_name;
                    let nodedown = thisCircles[i].down_name;
                    let source_node = thisCircles[i];
                    for (let j = 0; j < nodeup.length; j++) {
                        let target_node = nodesBarUp[this.vlist[0].flat().indexOf(nodeup[j])]
                        eachLinkUp = {
                            "active": false,
                            "source": source_node,
                            "target": {
                                "y": target_node.yu,
                                "x": target_node.xud
                            }
                        };

                        this.linksup.push(eachLinkUp)
                    }

                    for (let j = 0; j < nodedown.length; j++) {
                        let target_node = nodesBarDown[this.vlist[0].flat().indexOf(nodedown[j])]
                        eachLinkDown = {
                            "active": false,
                            "source": source_node,
                            "target": {
                                "y": target_node.yd,
                                "x": target_node.xud
                            }
                        };
                        this.linksdown.push(eachLinkDown)
                    }
                }

                let linkup = this.glinks.selectAll('links-up')
                    .data(this.linksup)
                    .enter()
                    .append('path')
                    .style("fill", "none")
                    .style("stroke", "grey")
                    .style("stroke-width", .1)
                    .style("opacity", function (d) {
                        return d.source.isvisible === true ? 0.5 : 0
                    })
                    .attr('d', linkVertical)

                let linkdown = this.glinks.selectAll('links-down')
                    .data(this.linksdown)
                    .enter()
                    .append('path')
                    .style("fill", "none")
                    .style("stroke", "grey")
                    .style("stroke-width", .1)
                    .style("opacity", function (d) {
                        return d.source.isvisible === true ? 0.5 : 0
                    })
                    .attr('d', linkVertical)

                let nodes = this.gscatter
                    .selectAll('circle')
                    .data(thisCircles)
                    .enter()
                    .append('circle')
                    .attr("r", function (d) {
                        return circleSize(d.relative)
                    })
                    .attr("cx", function (d) {
                        return d.x
                    })
                    .attr("cy", function (d) {
                        return d.y
                    })
                    .style('fill', 'grey')
                    .style('opacity', function (d) {
                        return d.isvisible === true ? 0.6 : 0
                    })
                    .on('click', onClickNodes)
                    .on('mouseover', onMouseoverNodes)
                    .on("mousemove", function(){
                        return d3.select('#tooltip1').style("top", (d3.event.pageY - 15) + "px" )
                            .style("left", (d3.event.pageX + 10) + "px" )})
                    .on("mouseout", onMouseoutNodes)
                    .on('dblclick', dblClickNodes);

                // ============================================
                //             add interactions
                // ============================================

                function onClickNodes(elemData) {
                    if (resetd === 0 || resetu === 0) {
                        nodesBarUp.forEach(x => {x.clicked = false, x.active= false});
                        nodesBarDown.forEach(x => {x.clicked = false, x.active= false});
                        resetd = 1;
                        resetu = 1;
                    }

                    let barsUpToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.up_names ? e.id : _.includes(elemData.up_name, Number(e.id)) ? e.id : 0
                        })
                    let barsDownToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.down_names ? e.id : _.includes(elemData.down_name, Number(e.id)) ? e.id : 0
                        })

                    barup
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[3]
                            }
                            else if (n.active === false && barsUpToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.active === false && barsUpToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.3
                            }
                        })

                    barupx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[3]
                            }
                            else if (n.active === false && barsUpToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })

                    bardown
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[2]
                            }
                            else if (n.active === false && barsDownToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.active === false && barsDownToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.3
                            }
                        })

                    bardownx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[2]
                            }
                            else if (n.active === false && barsDownToHighlight.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })

                    nodes
                        .style("opacity", function (node_d) {
                            if (node_d.clicked === true) {
                                return 1
                            }
                            else if (node_d.clicked === false && node_d === elemData) {
                                node_d.clicked = true
                                return 1
                            }
                            else if (node_d.clicked === false && node_d.isvisible === true) {
                                return 0.3
                            }
                            else {
                                return 0
                            }

                        })
                        .style("fill", function (node_d) {
                            if (node_d.clicked === true) {
                                return color[3]
                            }
                            else if (node_d.clicked === false && node_d === elemData) {
                                node_d.clicked = true
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })

                    linkup
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                return color[3]
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true) {
                                return 1
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return 1
                            }
                            else if (link_d.active === false && link_d.source.isvisible === true) {
                                return 0.3
                            }
                            else {
                                return 0
                            }
                        });

                    linkdown
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                return color[2]
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true) {
                                return 1
                            }
                            else if (link_d.active === false && link_d.source.index === elemData.index) {
                                link_d.active = true
                                return 1
                            }
                            else if (link_d.active === false && link_d.source.isvisible === true) {
                                return 0.3
                            }
                            else {
                                return 0
                            }
                        })
                }

                function onMouseoverNodes(elemData) {
                    let barsUpToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.up_names ? e.id : _.includes(elemData.up_name, Number(e.id)) ? e.id : 0
                        })
                    let barsDownToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.down_names ? e.id : _.includes(elemData.down_name, Number(e.id)) ? e.id : 0
                        })

                    barup
                        .style("fill", function (n) {
                            if (n.active === true || n.clicked === true) {
                                return color[3]
                            }
                            else if (barsUpToHighlight.indexOf(n.id) >= 0) {
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', function (n) {
                            if (n.active === true || n.clicked === true) {
                                return 1
                            }
                            else if (barsUpToHighlight.indexOf(n.id) >= 0) {
                                return 1
                            }
                            else {
                                return 0.3
                            }
                        })

                    barupx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[3]
                            }
                            else if (barsUpToHighlight.indexOf(n.id) >= 0) {
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })

                    bardown
                        .style("fill", function (n) {
                            if (n.active === true || n.clicked === true) {
                                return color[2]
                            }
                            else if (barsDownToHighlight.indexOf(n.id) >= 0) {
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', function (n) {
                            if (n.active === true || n.clicked === true) {
                                return 1
                            }
                            else if (barsDownToHighlight.indexOf(n.id) >= 0) {
                                return 1
                            }
                            else {
                                return 0.3
                            }
                        })

                    bardownx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[2]
                            }
                            else if (barsDownToHighlight.indexOf(n.id) >= 0) {
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })

                    nodes
                        .style("opacity", function (node_d) {
                            if (node_d.clicked === true || node_d.active === true) {
                                return 1
                            }
                            else if (node_d === elemData) {
                                return 1
                            }
                            else if (node_d.isvisible === true) {
                                return 0.3
                            }
                            else {
                                return 0
                            }

                        })
                        .style("fill", function (node_d) {
                            if (node_d.clicked === true || node_d.active === true) {
                                return color[3]
                            }
                            else if (node_d === elemData) {
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })

                    let highlightedNodes = thisCircles.map(function (e) {
                        return e.active === true ? e.index : -1
                    });

                    linkup
                        .style("stroke", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[3]
                            }
                            else if (link_d.source.index === elemData.index) {

                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 0.5
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 1
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 1
                            }
                            else if (link_d.source.isvisible === true) {
                                return 0.5
                            }
                            else {
                                return 0
                            }
                        });

                    linkdown
                        .style("stroke", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[2]
                            }
                            else if (link_d.source.index === elemData.index) {

                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 0.5
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 1
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 1
                            }
                            else if (link_d.source.isvisible === true) {
                                return 0.5
                            }
                            else {
                                return 0
                            }
                        })

                    d3.select("#tooltip1")
                        .style("visibility", "visible")
                        .text( elemData.relative)
                }

                function onMouseoutNodes(elemData) {
                    let barsUpToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.up_names ? e.id : _.includes(elemData.up_name, Number(e.id)) ? e.id : 0
                        })
                    let barsDownToHighlight = nodesBarUp
                        .map(function (e) {
                            return e.id === elemData.down_names ? e.id : _.includes(elemData.down_name, Number(e.id)) ? e.id : 0
                        })

                    barup
                        .style("fill", function (n) {
                            if (n.active === true || n.clicked === true) {
                                return color[3]
                            }
                            else if (barsUpToHighlight.indexOf(n.id) >= 0) {
                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', 1)
                        
                    barupx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[3]
                            }
                            else if (barsUpToHighlight.indexOf(n.id) >= 0) {
                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })

                    bardown
                        .style("fill", function (n) {
                            if (n.active === true || n.clicked === true) {
                                return color[2]
                            }
                            else if (barsDownToHighlight.indexOf(n.id) >= 0) {
                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style('opacity', 1)

                    bardownx
                        .style("fill", function (n) {
                            if (n.active === true) {
                                return color[2]
                            }
                            else if (barsDownToHighlight.indexOf(n.id) >= 0) {
                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })

                    nodes
                        .style("opacity", function (node_d) {
                            if (node_d.clicked === true || node_d.active === true) {
                                return 1
                            }
                            else if (node_d === elemData) {
                                return 0.6
                            }
                            else if (node_d.isvisible === true) {
                                return 0.6
                            }
                            else {
                                return 0
                            }

                        })
                        .style("fill", function (node_d) {
                            if (node_d.clicked === true || node_d.active === true) {
                                return color[3]
                            }
                            else if (node_d === elemData) {
                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })

                    let highlightedNodes = thisCircles.map(function (e) {
                        return e.active === true ? e.index : -1
                    });

                    linkup
                        .style("stroke", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[3]
                            }
                            else if (link_d.source.index === elemData.index) {

                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 0.5
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.1
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 1
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.5
                            }
                            else if (link_d.source.isvisible === true) {
                                return 0.5
                            }
                            else {
                                return 0
                            }
                        });

                    linkdown
                        .style("stroke", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[2]
                            }
                            else if (link_d.source.index === elemData.index) {

                                return "grey"
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 0.5
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.1
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (link_d.active === true || highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return 1
                            }
                            else if (link_d.source.index === elemData.index) {
                                return 0.5
                            }
                            else if (link_d.source.isvisible === true) {
                                return 0.5
                            }
                            else {
                                return 0
                            }
                        })
                    d3.select('#tooltip1').style("visibility", "hidden")
                }

                function dblClickNodes(elemData) {
                    let activeNumber = thisCircles.filter(x => x.active === true).length;
                    nodes.style('opacity', function (d) {
                        if (activeNumber > 0) {
                            d.clicked = false
                            return d.active === true? 1: d.isvisible === true || d.clicked === true? 0.3 : 0
                        }
                        else {
                            d.clicked = false
                            return d.isvisible === true? 0.6 : 0
                        }

                    }).style("fill", function (d) {
                        return d.active === true ? color[3] : "grey"
                    });

                    linkup.style("stroke", function (link_d) {
                        if (link_d.active === true) {
                            link_d.active = false
                            return "grey"
                        }
                        else if (link_d.source.active === true) {
                            return color[3]
                        }
                        else {
                            return "grey"
                        }
                    })
                        .style("stroke-width", function (link_d) {
                            if (link_d.source.active === true) {
                                link_d.active = false
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (activeNumber > 0) {
                                link_d.active = false
                                return link_d.source.active === true ? 1: link_d.source.isvisible === true || link_d.active === true? 0.8 : 0
                            }
                            else {
                                link_d.active = false
                                return link_d.source.isvisible === true? 0.5 : 0
                            }

                        })

                    linkdown.style("stroke", function (link_d) {
                        if (link_d.active === true) {
                            link_d.active = false
                            return "grey"
                        }
                        else if (link_d.source.active === true) {
                            return color[2]
                        }
                        else {
                            return "grey"
                        }
                    })
                        .style("stroke-width", function (link_d) {
                            if (link_d.source.active === true) {
                                link_d.active = false
                                return 0.5
                            }
                            else {
                                return 0.1
                            }
                        })
                        .style("opacity", function (link_d) {
                            if (activeNumber > 0) {
                                link_d.active = false
                                return link_d.source.active === true ? 1 : link_d.source.isvisible === true || link_d.active === true ? 0.8 : 0
                            }
                            else {
                                link_d.active = false
                                return link_d.source.isvisible === true ? 0.5 : 0
                            }
                        })

                    let highlightedNodes = thisCircles.map(function (e) {
                        return e.active === true ? e.index : -1
                    });
                    let activeBardown = _.union(_.flatten(thisCircles.filter(x => x.index === highlightedNodes.indexOf(x.index)).map(x => x.down_name)))
                    let highlightedBarDown = nodesBarDown
                        .map(function (e) {
                            return _.includes(activeBardown, Number(e.id)) ? e.id : -1
                        });
                    let activeBarup = _.union(_.flatten(thisCircles.filter(x => x.index === highlightedNodes.indexOf(x.index)).map(x => x.up_name)))
                    let highlightedBarUp = nodesBarUp
                        .map(function (e) {
                            return _.includes(activeBarup, Number(e.id)) ? e.id : -1
                        });

                    if (resetu === 0 && resetd === 1) { ////////////////////// clicking upbar
                        barup.style("fill", function (bar_d) {
                            if (bar_d.clicked === true) {
                                bar_d.clicked = false
                                return color[3]
                            }
                            else if (bar_d.active === true) {
                                bar_d.active = false
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                            .style('opacity', 1)

                        barupx.style("fill", function (bar_d) {
                            if (bar_d.clicked === true) {
                                bar_d.clicked = false
                                return color[3]
                            }
                            else if (bar_d.active === true) {
                                bar_d.active = false
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })


                        bardown.style("fill", function (n) {
                            return n.clicked === true? color[2] : "grey"
                        })
                            .style('opacity', 1)

                        bardownx.style("fill", function (n) {
                            return n.clicked === true? color[2] : "grey"
                        })
                    }
                    else if (resetd === 0 && resetu === 1) { ///////////////// clicking bottom bar
                        bardown.style("fill", function (bar_d) {
                            if (bar_d.clicked === true) {
                                bar_d.clicked = false
                                return color[2]
                            }
                            else if (bar_d.active === true) {
                                bar_d.active = false
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                            .style('opacity', 1)

                        bardownx.style("fill", function (bar_d) {
                            if (bar_d.clicked === true) {
                                bar_d.clicked = false
                                return color[2]
                            }
                            else if (bar_d.active === true) {
                                bar_d.active = false
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })

                        barup.style("fill", function (n) {
                            return n.clicked === true? color[3] : "grey"
                        })
                            .style('opacity', 1)

                        barupx.style("fill", function (n) {
                            return n.clicked === true? color[3] : "grey"
                        })
                    }
                    else {
                        bardown.style("fill", function (bar_d) {
                            bar_d.active = false
                            return "grey"
                        })
                            .style('opacity', 1)
                        bardownx.style("fill",function (bar_d) {
                            bar_d.active = false
                            return "grey"
                        })
                        barup.style("fill", function (bar_d) {
                            bar_d.active = false
                            return "grey"
                        })
                            .style('opacity', 1)
                        barupx.style("fill", function (bar_d) {
                            bar_d.active = false
                            return "grey"
                        })
                    }

                    d3.select('#tooltip1').style("visibility", "hidden")
                }

                function onClickBarUp(elemData) {
                    if (resetu === 1) {
                        nodesBarUp.forEach(x => {x.clicked = false, x.active = false});
                        nodesBarDown.forEach(x => {x.clicked = false, x.active = false});

                        resetu = 0;
                        resetd = 1;
                    }
                    thisCircles.forEach(x => {x.clicked = false, x.active = false});

                    barup
                        .style("fill", function (bar_d) {
                            if (bar_d.clicked === true && bar_d.id === elemData.id || bar_d.active === true) {
                                elemData.clicked = false;
                                return "grey"
                            }
                            else if (bar_d.clicked === false && bar_d.id === elemData.id) {
                                elemData.clicked = true;
                                return color[3]
                            }
                            else if (bar_d.clicked === true && bar_d.id !== elemData.id) {
                                return color[3]
                            }
                            else if (bar_d.clicked === false && bar_d.id !== elemData.id || bar_d.active === true) {
                                return "grey"
                            }
                        })
                        .style("opacity", function (bar_d) {
                            if (bar_d.clicked === false || bar_d.active === true) {
                                return 0.3
                            }
                            else if (bar_d.clicked === true) {
                                return 1
                            }
                        })

                    barupx
                        .style("fill", function (bar_d) {
                            if (bar_d.clicked === true && bar_d.id === elemData.id) {
                                return color[3]
                            }
                            else if (bar_d.clicked === false && bar_d.id === elemData.id) {
                                return "grey"
                            }
                            else if (bar_d.clicked === true && bar_d.id !== elemData.id) {
                                return color[3]
                            }
                            else if (bar_d.clicked === false && bar_d.id !== elemData.id) {
                                return "grey"
                            }
                        });

                    let highlightedBarUp = nodesBarUp.filter(e => e.clicked === true).map(e => Number(e.id)).toString();

                    nodes
                        .style("opacity", function (node_d) {
                            if (node_d.up_name.toString() === highlightedBarUp && node_d.isvisible === true) {
                                node_d.active = true;
                                return 1
                            }
                            else {
                                node_d.active = false;
                                if (node_d.isvisible === true) {
                                    return 0.3
                                } else {
                                    return 0
                                }

                            }
                        })
                        .style("fill", function (node_d) {
                            return node_d.up_name.toString() === highlightedBarUp ? color[3] : "grey"
                        });


                    let highlightedNodes = thisCircles.map(function (e) {
                        return e.active === true ? e.index : -1
                    });

                    linkup
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                link_d.active = false
                                return "grey"
                            }
                            else if (highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 0.5 : 0.1;
                        })
                        .style("opacity", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 1 : link_d.source.isvisible === true ? 0.5 : 0;
                        });

                    linkdown
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                link_d.active = false
                                return "grey"
                            }
                            else if (highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 0.5 : 0.1;
                        })
                        .style("opacity", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 1 : link_d.source.isvisible === true ? 0.5 : 0;
                        });

                    let activeBar = _.union(_.flatten(thisCircles.filter(x => x.index === highlightedNodes.indexOf(x.index)).map(x => x.down_name)))
                    let highlightedBarDown = nodesBarDown
                        .map(function (e) {
                            return _.includes(activeBar, Number(e.id)) ? e.id : -1
                        });

                    bardown
                        .style("fill", function (n) {
                            if (highlightedBarDown.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[2]
                            }
                            else {
                                n.active = false
                                return "grey"
                            }

                        })
                        .style("opacity", function (n) {
                             if (highlightedBarDown.indexOf(n.id) >= 0) {
                                n.active = true
                                return 1
                            }
                            else {
                                n.active = false
                                return 0.3
                            }
                        })

                    bardownx
                        .style("fill", function (n) {
                             if (highlightedBarDown.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[2]
                            }
                            else {
                                n.active = false
                                return "grey"
                            }
                        })
                }

                function onClickBarDown(elemData) {
                    if (resetd === 1) {
                        nodesBarUp.forEach(x => {x.clicked = false, x.active = false});
                        nodesBarDown.forEach(x => {x.clicked = false, x.active = false});
                        resetd = 0;
                        resetu = 1;
                    }
                    thisCircles.forEach(x => {x.clicked = false, x.active = false});

                    bardown
                        .style("fill", function (bar_d) {
                            if (bar_d.clicked === true && bar_d.id === elemData.id || bar_d.active === true) {
                                elemData.clicked = false;
                                return "grey"
                            }
                            else if (bar_d.clicked === false && bar_d.id === elemData.id) {
                                elemData.clicked = true;
                                return color[2]
                            }
                            else if (bar_d.clicked === true && bar_d.id !== elemData.id) {
                                return color[2]
                            }
                            else if (bar_d.clicked === false && bar_d.id !== elemData.id || bar_d.active === true) {
                                return "grey"
                            }

                        })
                        .style("opacity", function (bar_d) {
                            if (bar_d.clicked === false || bar_d.active === true) {
                                return 0.3
                            }
                            else if (bar_d.clicked === true) {
                                return 1
                            }
                        })

                    bardownx
                        .style("fill", function (bar_d) {
                            if (bar_d.clicked === true && bar_d.id === elemData.id) {
                                return color[2]
                            }
                            else if (bar_d.clicked === false && bar_d.id === elemData.id) {
                                return "grey"
                            }
                            else if (bar_d.clicked === true && bar_d.id !== elemData.id) {
                                return color[2]
                            }
                            else if (bar_d.clicked === false && bar_d.id !== elemData.id) {
                                return "grey"
                            }
                        })

                    let highlightedBarDown = nodesBarDown.filter(e => e.clicked === true).map(e => Number(e.id)).toString()

                    nodes
                        .style("opacity", function (node_d) {
                            if (node_d.down_name.toString() === highlightedBarDown && node_d.isvisible === true) {
                                node_d.active = true;
                                return 1
                            } else {
                                node_d.active = false;
                                if (node_d.isvisible === true) {
                                    return 0.3
                                } else {
                                    return 0
                                }
                            }
                        })
                        .style("fill", function (node_d) {
                            return node_d.down_name.toString() === highlightedBarDown ? color[3] : "grey"
                        })


                    let highlightedNodes = thisCircles.map(function (e) {
                        return e.active === true ? e.index : -1
                    })

                    linkdown
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                link_d.active = false
                                return "grey"
                            }
                            else if (highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[2]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 0.5 : 0.1;
                        })
                        .style("opacity", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 1 : link_d.source.isvisible === true ? 0.5 : 0;
                        });

                    linkup
                        .style("stroke", function (link_d) {
                            if (link_d.active === true) {
                                link_d.active = false
                                return "grey"
                            }
                            else if (highlightedNodes.indexOf(link_d.source.index) >= 0) {
                                return color[3]
                            }
                            else {
                                return "grey"
                            }
                        })
                        .style("stroke-width", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 0.5 : 0.1;
                        })
                        .style("opacity", function (link_d) {
                            return highlightedNodes.indexOf(link_d.source.index) >= 0 ? 1 : link_d.source.isvisible === true ? 0.5 : 0;
                        });


                    let activeBar = _.union(_.flatten(thisCircles.filter(x => x.index === highlightedNodes.indexOf(x.index)).map(x => x.up_name)))
                    let highlightedBarUp = nodesBarUp
                        .map(function (e) {
                            return _.includes(activeBar, Number(e.id)) ? e.id : -1
                        })

                    barup
                        .style("fill", function (n) {
                            if (highlightedBarUp.indexOf(n.id) >= 0 ) {
                                n.active = true
                                return color[3]
                            }
                            else {
                                n.active = false
                                return "grey"
                            }

                        })
                        .style("opacity", function (n) {
                            if (highlightedBarUp.indexOf(n.id) >= 0) {
                                n.active = true
                                return 1
                            }
                            else {
                                n.active = false
                                return 0.3
                            }
                        })

                    barupx
                        .style("fill", function (n) {
                            if (highlightedBarUp.indexOf(n.id) >= 0) {
                                n.active = true
                                return color[3]
                            }
                            else {
                                n.active = false
                                return "grey"
                            }
                        })
                }

                function dblClickBars() {
                    barup
                        .style("fill", function (bar_d) {
                            bar_d.active = false
                            bar_d.clicked = false
                            return "grey"
                        })
                        .style('opacity', 1)

                    barupx
                        .style("fill", "grey")

                    bardown
                        .style("fill", function (bar_d) {
                            bar_d.active = false
                            bar_d.clicked = false
                            return "grey"
                        })
                        .style('opacity', 1)

                    bardownx
                        .style("fill", "grey")


                    nodes
                        .style("fill", function (d) {
                            d.active = false
                            d.clicked = false
                            return "grey"

                        })
                        .style("opacity", function (d) {
                            if (d.active === true ||  d.isvisible === true) {
                                return 0.6
                            }
                            else return 0
                        })


                    linkup
                        .style("stroke", "grey")
                        .style("stroke-width",function (d) {
                            if (d.source.isvisible === true) {
                                return 0.1
                            }
                            else {
                                return 0
                            }
                        })
                        .style("opacity", function (d) {
                            if (d.source.isvisible === true) {
                                return 0.8
                            }
                            else {
                                return 0
                            }
                        });

                    linkdown
                        .style("stroke", "grey")
                        .style("stroke-width", function (d) {
                            if (d.source.isvisible === true) {
                                return 0.1
                            }
                            else {
                                return 0
                            }
                        })
                        .style("opacity", function (d) {
                            if (d.source.isvisible === true) {
                                return 0.5
                            }
                            else {
                                return 0
                            }
                        })
                }
            },
        },


        created() {
            this.Nn = this.variableList.length;
            this.getNodes(this.Nn);
            let nn = this.vlist[0].flat();
            this.getCircles(nn);
        }
    }
</script>

<style scoped>
    div {
        background-color: white;
        margin-top: 10px;
    }

    .title {
        padding-top: 5px;
        padding-bottom: 5px;
        padding-left: 5px;
    }

    h6 {
        margin-bottom: 0px;
        font-size: 20px;
    }

    p {
        margin-bottom: 5px;
        font-size: 18px;
        color: grey;
    }

    hr {
        margin-top: 5px;
        width: 99%;
        margin-bottom: 20px;
    }

    .scatter-view-container {
        padding-top: 0px;
        padding-bottom: 0px;
        padding-left: 0px;
        padding-right: 0px;
        margin-left: 0px;
        margin-right: 0px;
        margin-top: 0px;
    }

    .slidecontainer {
        width: 55%; /* Width of the outside container */
        margin-left: 0px;
        margin-right: 0px;
        text-align: center;
    }

    .sliders {
        margin-top: 0px;
        margin-bottom: 5px;
        text-align: center;
    }

    .sliders input {
        margin-left: 0px;
        margin-right: 10px;
        margin-top: 0px;
        margin-bottom: 0px;
    }

    /* The slider itself */
    .slider {
        width: 55%; /* Full-width */
        /*height: 25px; !* Specified height *!*/
        background: #d3d3d3; /* Grey background */
        outline: none; /* Remove outline */
        opacity: 0.7; /* Set transparency (for mouse-over effects on hover) */
        -webkit-transition: .2s; /* 0.2 seconds transition on hover */
        transition: opacity .2s;
        margin-top:0px;
        vertical-align: middle;
    }

    span {
        float:right;
    }

    div .name {
        padding-top: 5px;
    }

    .btn-sm, .btn-group-sm > .btn {
        font-size: 18px !important;
    }

</style>
