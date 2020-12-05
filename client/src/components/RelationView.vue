<template>
    <div id="relation-view">
        <b-row class="relation-view-container">
            <b-col cols="10" class="indices-container">
                <b-col class="main-cols">
                    <b-row class="button">
                        <b-col class="button-super" cols="3">
                            <p><b>| Super Indices |</b></p>
                        </b-col>
                        <b-col class="button-sobol" cols="3">
                            <p><b>| Sobol Indices |</b></p>
                        </b-col>
                        <b-col class="button-closed" cols="3">
                            <p><b>| Closed Indices |</b></p>
                        </b-col>
                        <b-col class="button-total" cols="3">
                            <p><b>| Total Indices |</b></p>
                        </b-col>
                    </b-row>
                    <hr>
                    <b-row class="main-svg">
                        <svg id="v-parallel"></svg>
                    </b-row>

                </b-col>
            </b-col>
            <b-col cols="2" class="label-container">
                <b-row class="button">
                    <b-col class="button-label">
                        <p><b>| Labels |</b></p>
                    </b-col>
                </b-row>
                <hr>

                <b-row class="main-label">
                    <svg id="label"></svg>
                </b-row>

            </b-col>

        </b-row>

    </div>
    
</template>

<script>
    import * as d3 from "d3";
    import _ from "lodash";
    import {combinations} from '@/functionality/permutations'
    import * as loom from "d3-loom"



    export default {
        name: "RelationView",
        props: {
            items: Array,
            variableList: Array,
            input: Array,
            // N: Number
        },
        data() {
            return {
                N: null,
                title: "Relation View",
                vlist: this.variableList,
                values: this.items,
                nodes: [],
                closed_links: [],
                total_links: [],
                super_links: [],
                linksLeft: [],
                linksRight: [],
                linksTotal: [],

            }
        },
        watch: {
            variableList: {
                immediate: true,
                handler() {
                    this.vlist = this.variableList;
                }
            },
            items: {
                immediate: true,
                handler() {
                    this.values = this.items;
                    this.N = this.items.length;

                    if (this.gclosed) {
                        this.gclosed.selectAll("rect").remove();
                        this.gclosed.selectAll("text").remove();
                        this.gsuper.selectAll("rect").remove();
                        this.gsuper.selectAll("text").remove();
                        this.gsobol.selectAll("rect").remove();
                        this.gsobol.selectAll("text").remove();
                        this.gtotal.selectAll("path").remove();
                        this.gtotal.selectAll("circle").remove();
                        this.glinks.selectAll("path").remove();
                        this.glabel.selectAll("text").remove();
                        this.nodes = [];
                        this.closed_links = [];
                        this.super_links = [];
                        this.total_links = [];
                        this.linksLeft = [];
                        this.linksRight = [];
                        this.linksTotal = [];
                        this.graph = {};

                        this.getNodes(this.N);
                        this.getClosedLinks(this.N);
                        this.getSuperLinks(this.N);
                        this.getTotalLinks(this.N);
                        this.drawChart();
                    }

                }
            },
            N: function (newData) {
                this.gclosed.selectAll("rect").remove();
                this.gclosed.selectAll("text").remove();
                this.gsuper.selectAll("rect").remove();
                this.gsuper.selectAll("text").remove();
                this.gsobol.selectAll("rect").remove();
                this.gsobol.selectAll("text").remove();
                this.gtotal.selectAll("path").remove();
                this.gtotal.selectAll("circle").remove();
                this.glinks.selectAll("path").remove();
                this.glabel.selectAll("text").remove();
                this.nodes = [];
                this.closed_links = [];
                this.super_links = [];
                this.total_links = [];
                this.linksLeft = [];
                this.linksRight = [];
                this.linksTotal = [];
                this.graph = {};

                this.getNodes(newData);
                this.getClosedLinks(newData);
                this.getSuperLinks(newData);
                this.getTotalLinks(newData);
                this.drawChart();
            }
        },

        mounted() {
            const body = document.body;
            const screenWidth = body.scrollWidth, screenHeight = body.scrollHeight;
            this.margins = {top: 10, right: 0, bottom: 60, left: 0};
            this.width = (screenWidth*8/12)*10/12 - this.margins.left - this.margins.right;
            this.marginlL = {top: 10, right: 20, bottom: 60, left: 8};
            this.height = (screenHeight-65) - this.margins.top - this.margins.bottom;
            this.widthL = (screenWidth*8/12)*2/12 - this.marginlL.left - this.marginlL.right;

            let svg = d3.select("svg#v-parallel")
                .attr("height", this.height + this.margins.top + this.margins.bottom)
                .attr("width", this.width + this.margins.left + this.margins.right)
                .attr("transform", "translate(" + this.margins.left + "," + this.margins.top + ")");

            this.gsuper = svg.append('g')
                .attr('class', 'super');

            this.gsobol = svg.append('g')
                .attr('class', 'sobol');

            this.gclosed = svg.append('g')
                .attr('class', 'closed');

            this.gtotal = svg.append("g")
                .attr('class', 'total');

            this.glinks = svg.append('g')
                .attr('class', 'links');

            let svglabel = d3.select("svg#label")
                .attr("height", this.height + this.marginlL.top + this.marginlL.bottom)
                .attr("width", this.widthL + this.marginlL.left + this.marginlL.right);

            this.glabel = svglabel.append("g")
                .attr("transform", "translate(" + this.marginlL.left + "," + this.marginlL.top + ")")
                .attr('class', 'label');



            this.drawChart();

        },

        methods: {
            getNodes(n) {
                let acc_nodes = 0;
                for (let i = 0; i < n; i++) {
                    let order = i + 1;
                    let node = {};

                    for (let j = 0; j < this.vlist[i].length; j++) {
                        let v_name = this.vlist[i][j];
                        let dc = this.values[i]['dc'][j];
                        let sobol_value = this.values[i]['sobol'][j];
                        let sobol_closed = this.values[i]['closed'][j];
                        let sobol_total = this.values[i]['total'][j];
                        let sobol_super = this.values[i]['super'][j];

                        node = {
                            "name": v_name.join("_"),
                            "dc": dc,
                            "sobol": sobol_value,
                            "closed": sobol_closed,
                            "total": sobol_total,
                            "ssuper": sobol_super,
                            "grp": order, // the group each node belongs to
                            "id": v_name.join("_"),
                            "clicked": false, // mark for clicked
                            "active": false, // mark for highlighted
                        };
                        
                        if (i > 0 && j === 0) {
                            let order_len_pre = this.vlist[i - 1].length;
                            acc_nodes = acc_nodes + order_len_pre;
                        }
                        this.nodes[acc_nodes + j] = node;

                    }
                }
            },

            getClosedLinks(n) {
                for (let i = 0; i < n; i++) {
                    let closed_link = {};

                    for (let j = 0; j < this.vlist[i].length; j++) {
                        let v_name = this.vlist[i][j];
                        let subsets = [];

                        if (v_name.length === 1) {
                            subsets.push(v_name)
                        }

                        for (let k = 0; k < v_name.length; k++) {
                            let subset = combinations(v_name, k + 1);
                            subsets.push(subset);
                        }
                        subsets = subsets.flat();

                        for (let k = 0; k < subsets.length; k++) {

                            closed_link = {
                                "source": subsets[k].length >= 2 ? subsets[k].join("_") : subsets[k].toString(),
                                "target": v_name.length >= 2 ? v_name.join("_") : v_name.toString(),
                                "value": subsets[k].length >= 2 ?
                                    this.nodes.filter(x => x.id === subsets[k].join("_")).map(x => x.sobol) :
                                    this.nodes.filter(x => x.id === subsets[k].toString()).map(x => x.sobol),
                                "active": false
                            };
                            this.closed_links.push(closed_link);
                        }


                    }
                }
            },

            getSuperLinks(n) {
                const total_set = this.vlist[0].flat()//_.range(1, this.N + 1);
                for (let i = 0; i < n; i++) {
                    let super_link = {};
                    for (let j = 0; j < this.vlist[i].length; j++) {
                        let v_name = this.vlist[i][j];
                        let rim_set = total_set;
                        for (let k = 0; k < v_name.length; k++) {
                            let temp = _.without(rim_set, v_name[k]);
                            rim_set = temp
                        }
                        let subsets = [];
                        subsets.push(Array([...v_name]));
                        for (let k = 0; k < rim_set.length; k++) {
                            let subset = combinations(rim_set, k + 1);
                            // loop through all the sebsets and add v_name to each of them, then sort it to make it ready for constructing links
                            let subsett = subset.map(set => {
                                let sett = set.concat(v_name);
                                return sett.sort(function (a, b) {
                                    return a - b;
                                })
                            });
                            subsets.push(subsett);
                        }
                        for (let k = 0; k < subsets.length; k++) {
                            for (let m = 0; m < subsets[k].length; m++) {
                                super_link = {
                                    "source": subsets[k][m].length >= 2 ? subsets[k][m].join("_") : subsets[k][m].toString(),
                                    "target": v_name.length >= 2 ? v_name.join("_") : v_name.toString(),
                                    "value": subsets[k][m].length >= 2 ?
                                        this.nodes.filter(x => x.id === subsets[k][m].join("_")).map(x => x.sobol) :
                                        this.nodes.filter(x => x.id === subsets[k][m].toString()).map(x => x.sobol),
                                    "active": false
                                };
                                this.super_links.push(super_link);
                            }

                        }

                    }
                }
            },

            getTotalLinks(n) {
                const total_set = this.vlist[0].flat()//_.range(1, NN + 1); // [1,2,3,4,5,6]
                let whole_subset = [];
                for (let i = 0; i < total_set.length; i++) {
                    let tem_subset = combinations(total_set, i + 1);
                    whole_subset.push(tem_subset)
                }
                for (let i = 0; i < n; i++) {
                    let total_link = {};
                    for (let j = 0; j < this.vlist[i].length; j++) {
                        let v_name = this.vlist[i][j]; // [1,2]
                        let rim_set = total_set;
                        for (let k = 0; k < v_name.length; k++) {
                            let temp = _.without(rim_set, v_name[k]);
                            rim_set = temp // [3,4,5,6]
                        }
                        let rim_subset = [];
                        for (let k = 0; k < rim_set.length; k++) {
                            let tem_subset = combinations(rim_set, k + 1);
                            rim_subset.push(tem_subset)
                        }
                        rim_subset = rim_subset.flat().map(x => x.join("_"));
                        let super_set = whole_subset.flat().map(x => x.join("_")).filter(a => !rim_subset.includes(a));

                        for (let k = 0; k < super_set.length; k++) {
                            total_link = {
                                "source": super_set[k],
                                "target": v_name.length >= 2 ? v_name.join("_") : v_name.toString(),
                                "value": this.nodes.filter(x => x.id === super_set[k]).map(x => x.sobol),
                                "active": false
                            };
                            this.total_links.push(total_link);
                        }
                    }
                }
            },

            drawChart() {
                const height = this.height;
                const width = this.width;


                // A color scale for groups: // define your own color mapping function
                const color = ['#2ca8bd', '#28a744', '#a157a6', '#dc3445'];
                const color_links = ['#2ca8bd', '#b3de69', '#bc80bd', '#dc3445'];  // new links color

                // A linear scale for node size
                const size = d3.scaleLinear()
                    .domain([0, 1])
                    .range([0, 90]); // from 30 to 90, so avoid times 3 afterwards all the time

                const sizelink = d3.scalePow()
                    .exponent(0.2)
                    .domain([0, 1])
                    .range([0, 5]);

                let nodes_super = _.cloneDeep(this.nodes);
                let nodes_sobol = _.cloneDeep(this.nodes);
                let nodes_closed = _.cloneDeep(this.nodes);
                let nodes_total = _.cloneDeep(this.nodes);
                let nodes_label = _.cloneDeep(this.nodes);


                let graph = {
                    "nodes_super": nodes_super,
                    "nodes_sobol": nodes_sobol,
                    "nodes_closed": nodes_closed,
                    "nodes_total": nodes_total,
                    "nodes_label": nodes_label,
                    "closed_links": this.closed_links,
                    "super_links": this.super_links,
                    "total_links": this.total_links
                };

                let allNodes = graph.nodes_super.map(function (d) {
                    return d.name
                });

                // A linear scale to position the nodes on the Y axis
                const y = d3.scalePoint()
                    .range([20, height])
                    .domain(allNodes);

                // use scale band for bar chart
                const yScale = d3.scaleBand()
                    .range([20, height])
                    .domain(allNodes)
                    .padding(.85)
                    .round(true);

                // Add the horizontal bars for super indices
                let barsSuper = this.gsuper
                    .selectAll("super-bars")
                    .data(graph.nodes_super)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.bandwidth())
                    .attr("x", function (d) {
                        return (90 - size(d.ssuper))
                    })
                    .attr("width", function (d) {
                        return (size(d.ssuper))
                    })
                    .style("fill", color[0])

                let superValue = this.gsuper
                    .selectAll("labels")
                    .data(graph.nodes_super)
                    .enter()
                    .append("text")
                    .attr("x", 0)
                    .attr("y", yScale.bandwidth() + 1 )
                    .text(function (d) {
                        return (d.ssuper)
                    })
                    .style("text-anchor", "end")
                    .attr("transform", function (d) {
                        return ("translate(" + (90) + "," + (y(d.name) + yScale.step()/2) + ")")
                    })
                    .style("font-size", 18)
                    .style("opacity", 0);

                let barsSuperbg = this.gsuper
                    .selectAll("super-bars")
                    .data(graph.nodes_super)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.step())
                    .attr("x", 0)
                    .attr("width", function (d) {
                        return (size(1))
                    })
                    .style("fill", "#cccccc")
                    .style('opacity', 0)
                    .on('click', onClickSuper)
                    .on('mouseover', onMouseoverSuper)
                    .on('dblclick', onReleaseSuper);

                // Add the horizontal bars for the closed indices
                let barsClosed = this.gclosed
                    .selectAll("closed-bars")
                    .data(graph.nodes_closed)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.bandwidth())
                    .attr("x", width*3/4 - 90)
                    .attr("width", function (d) {
                        return (size(d.closed))
                    })
                    .style("fill", function (d) {
                        return color[1]
                    })

                let closedValue = this.gclosed
                    .selectAll("labels")
                    .data(graph.nodes_closed)
                    .enter()
                    .append("text")
                    .attr("x", 0)
                    .attr("y", yScale.bandwidth() +1)
                    .text(function (d) {
                        return (d.closed)
                    })
                    .style("text-anchor", "start")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/4 - 90) + "," + (y(d.name) + yScale.step()/2) + ")")
                    })
                    .style("font-size", 18)
                    .style("opacity", 0);

                let barsClosedbg = this.gclosed
                    .selectAll("closed-bars")
                    .data(graph.nodes_closed)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.step())
                    .attr("x", width*3/4 - 90)
                    .attr("width",  size(1))
                    .style("fill", "#cccccc")
                    .style('opacity', 0)
                    .on('click', onClickClosed)
                    .on('mouseover', onMouseoverClosed)
                    .on('dblclick', onReleaseClosed);

                // Add the horizontal bar for the sobol indices
                let barsSobol = this.gsobol
                    .selectAll("sobol-bars")
                    .data(graph.nodes_sobol)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.bandwidth())
                    .attr("x", function(d) {
                        return width*3/8 - size(d.sobol)/2
                    })
                    .attr("width", function (d) {
                        return (size(d.sobol))
                    })
                    .style("fill", color[3])

                let sobolValue = this.gsobol
                    .selectAll("labels")
                    .data(graph.nodes_sobol)
                    .enter()
                    .append("text")
                    .attr("x", 0)
                    .attr("y", yScale.bandwidth() + 1 )
                    .text(function (d) {
                        return (d.sobol)
                    })
                    .style("text-anchor", "middle")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/8) + "," + (y(d.name) + yScale.step()/2) + ")")
                    })
                    .style("font-size", 18)
                    .style("opacity", 0);

                let barsSobolbg = this.gsobol
                    .selectAll("sobol-bars")
                    .data(graph.nodes_sobol)
                    .enter()
                    .append("rect")
                    .attr("y", function (d) {
                        return (y(d.name) )
                    })
                    .attr("height", yScale.step())
                    .attr("x", function(d) {
                        return width*3/8 - size(1)/2
                    })
                    .attr("width", size(1))
                    .style("fill", "#cccccc")
                    .attr("opacity", 0)
                    .on('click', onClickSobol)
                    .on('mouseover', onMouseoverSobol)
                    .on('dblclick', onReleaseSobol);


                // Add arcs for the total indices and others
                // set constants
                const PI = Math.PI;
                let arcWidth = yScale.bandwidth() > 5 ? 5 : yScale.bandwidth()*4/6; // width
                let arcPad = .5; // padding between arcs

                // arc accessor
                //  d and i are automatically passed to accessor functions,
                //  with d being the data and i the index of the data
                let drawArcTotal = d3.arc()
                    .innerRadius(arcWidth*3+arcPad)
                    .outerRadius(arcWidth*4)
                    .startAngle(0)
                    .endAngle(function (d, i) {return d.total*360 * (PI / 180);});

                let drawArcClosed = d3.arc()
                    .innerRadius(arcWidth*2+arcPad)
                    .outerRadius(arcWidth*3)
                    .startAngle(0)
                    .endAngle(function (d, i) {return d.closed*360 * (PI / 180);});

                let drawArcSuper = d3.arc()
                    .innerRadius(arcPad)
                    .outerRadius(arcWidth)
                    .startAngle(function (d, i) {return (d.closed-d.sobol)*360 * (PI / 180);})
                    .endAngle(function (d, i) {return (d.closed-d.sobol + d.ssuper)*360 * (PI / 180);});

                let drawArcSobol = d3.arc()
                    .innerRadius(arcPad+arcWidth)
                    .outerRadius(arcWidth*2)
                    .startAngle(function (d, i) {return (d.closed-d.sobol)*360 * (PI / 180);})
                    .endAngle(function (d, i) {return d.closed*360 * (PI / 180);});

                let tooltip = d3.select('body').append('div')
                    .attr("id", 'tooltip')
                    .style("position", 'absolute')
                    .style("z-index", "10")
                    .style("visibility", "hidden")

                let arcsbg = this.gtotal
                    .selectAll("total-bars")
                    .data(graph.nodes_total)
                    .enter()
                    .append("circle")
                    .attr("cy", function (d) {
                        return (y(d.name) + yScale.bandwidth()/2)
                    })
                    .attr("r", arcWidth*4)
                    .attr("cx", width*3/4 + 20)
                    .style("fill", "#eeeeee")
                    .on("mouseover", onMouseoverTotal)
                    .on("mousemove", function(){
                        return d3.select('#tooltip').style("top", (d3.event.pageY +30 ) + "px" )
                            .style("left", (d3.event.pageX - 20) + "px" )})
                    .on("mouseout", onMouseoutTotal)


                let arcsTotal = this.gtotal
                    .selectAll("total-arcs")
                    .data(graph.nodes_total)
                    .enter()
                    .append("path")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/4 + 20) + "," + (y(d.name) + yScale.bandwidth()/2) + ")")
                    })
                    .attr("d", drawArcTotal)
                    .attr("fill", color[2])
                    .on("mouseover", onMouseoverTotal)
                    .on("mousemove", function(){
                        return d3.select('#tooltip').style("top", (d3.event.pageY +30 ) + "px" )
                            .style("left", (d3.event.pageX - 20) + "px" )})
                    .on("mouseout", onMouseoutTotal)


                let arcsClosed = this.gtotal
                    .selectAll("closed-arcs")
                    .data(graph.nodes_total)
                    .enter()
                    .append("path")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/4 + 20) + "," + (y(d.name) + yScale.bandwidth()/2) + ")")
                    })
                    .attr("d", drawArcClosed)
                    .attr("fill", color[1])
                    .on("mouseover", onMouseoverTotal)
                    .on("mousemove", function(){
                        return d3.select('#tooltip').style("top", (d3.event.pageY +30 ) + "px" )
                            .style("left", (d3.event.pageX - 20) + "px" )})
                    .on("mouseout", onMouseoutTotal)


                let arcsSuper = this.gtotal
                    .selectAll("super-arcs")
                    .data(graph.nodes_total)
                    .enter()
                    .append("path")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/4 + 20) + "," + (y(d.name) + yScale.bandwidth()/2) + ")")
                    })
                    .attr("d", drawArcSuper)
                    .attr("fill", color[0])
                    .on("mouseover", onMouseoverTotal)
                    .on("mousemove", function(){
                        return d3.select('#tooltip').style("top", (d3.event.pageY +30 ) + "px" )
                            .style("left", (d3.event.pageX - 20) + "px" )})
                    .on("mouseout", onMouseoutTotal)


                let arcsSobol = this.gtotal
                    .selectAll("sobol-arcs")
                    .data(graph.nodes_total)
                    .enter()
                    .append("path")
                    .attr("transform", function (d) {
                        return ("translate(" + (width*3/4 + 20) + "," + (y(d.name) + yScale.bandwidth()/2) + ")")
                    })
                    .attr("d", drawArcSobol)
                    .attr("fill", color[3])
                    .on("mouseover", onMouseoverTotal)
                    .on("mousemove", function(){
                        return d3.select('#tooltip').style("top", (d3.event.pageY +30 ) + "px" )
                            .style("left", (d3.event.pageX - 20) + "px" )})
                    .on("mouseout", onMouseoutTotal)



                // =============================================
                //                    add links
                // =============================================


                // define link type
                let link_horizontal = d3.linkHorizontal()
                    .x(function (d) {
                        return d.x;
                    })
                    .y(function (d) {
                        return d.y;
                    });

                // compute links position
                let eachLinkLeft = {};
                for (let i = 0; i < this.super_links.length; i++) {
                    let linkLeftSource = this.super_links[i].source;
                    let linkLeftTarget = this.super_links[i].target;

                    let sourcelSobol = this.super_links[i].value;
                    let sourceX = width*3/8 - size(sourcelSobol)/2;
                    let sourceY = y(linkLeftSource) + yScale.bandwidth()/2
                    let targetX = 90;
                    let targetY = y(linkLeftTarget) + yScale.bandwidth()/2

                    eachLinkLeft = {
                        "value": sourcelSobol,
                        "active": this.super_links[i].active,
                        "source": {
                            "source": linkLeftSource,
                            "y": sourceY,
                            "x": sourceX
                        },
                        "target": {
                            "target": linkLeftTarget,
                            "y": targetY,
                            "x": targetX
                        }
                    };

                    this.linksLeft.push(eachLinkLeft)


                }

                let eachLinkRight = {}
                for (let i = 0; i < this.closed_links.length; i++) {
                    let linkRightSource = this.closed_links[i].source;
                    let linkRightTarget = this.closed_links[i].target;

                    let sourcerSobol = this.closed_links[i].value;
                    let sourceX = width*3/8 + size(sourcerSobol)/2;
                    let sourceY = y(linkRightSource) + yScale.bandwidth()/2
                    let targetX = width*3/4 - 90;
                    let targetY = y(linkRightTarget) + yScale.bandwidth()/2

                    eachLinkRight = {
                        "value": sourcerSobol,
                        "active": this.closed_links[i].active,
                        "source": {
                            "source":linkRightSource,
                            "y": sourceY,
                            "x": sourceX
                        },
                        "target": {
                            "target": linkRightTarget,
                            "y": targetY,
                            "x": targetX
                        }
                    };

                    this.linksRight.push(eachLinkRight)
                }

                // ========== construct total links ============
                let eachLinkTotal = {}
                for (let i = 0; i < this.total_links.length; i++) {
                    let linkTotalSource = this.total_links[i].source;
                    let linkTotalTarget = this.total_links[i].target;

                    let sourcetSobol = this.total_links[i].value;
                    let sourceX = width-10;
                    let sourceY = y(linkTotalSource) + yScale.bandwidth()/2;
                    let targetX = width*3/4 + 40;
                    let targetY = y(linkTotalTarget) + yScale.bandwidth()/2;

                    eachLinkTotal = {
                        "value": sourcetSobol,
                        "active": this.total_links[i].active,
                        "source": {
                            "source":linkTotalSource,
                            "y": sourceY,
                            "x": sourceX
                        },
                        "target": {
                            "target": linkTotalTarget,
                            "y": targetY,
                            "x": targetX
                        }
                    };

                    this.linksTotal.push(eachLinkTotal)
                }

                // add total links
                let linkTotal = this.glinks
                    .selectAll('total-links')
                    .data(this.linksTotal)
                    .enter()
                    .append('path')
                    .attr('d', link_horizontal)
                    .style("fill", "none")
                    .style("stroke", color_links[2])
                    .style("stroke-opacity", 0.1)
                    .style("stroke-width", function (d) {
                        return sizelink(d.value)
                    })

                // add left links
                let linkLeft = this.glinks
                    .selectAll('left-links')
                    .data(this.linksLeft)
                    .enter()
                    .append('path')
                    .attr('d', link_horizontal)
                    .style("fill", "none")
                    .style("stroke", color_links[0])
                    .style("stroke-opacity", .2)
                    .style("stroke-width", function (d) {
                        return sizelink(d.value)
                    })

                // add right links
                let linkRight = this.glinks
                    .selectAll('right-links')
                    .data(this.linksRight)
                    .enter()
                    .append('path')
                    .attr('d', link_horizontal)
                    .style("fill", "none")
                    .style("stroke", color_links[1])
                    .style("stroke-opacity", 0.2)
                    .style("stroke-width", function (d) {
                        return sizelink(d.value)
                    })

                let onenode = graph.nodes_label.filter(x => graph.nodes_label.indexOf(x) === 0)
                let label_line = this.glabel
                    .selectAll("line")
                    .data(onenode)
                    .enter()
                    .append("line")
                    .attr("x1", this.widthL/2)
                    .attr("y1", function (d) {
                        return y(d.name)
                    })
                    .attr("x2", this.widthL/2)
                    .attr("y2", this.height+yScale.bandwidth())
                    .style("stroke-width", 0.3)
                    .style("stroke", "#cccccc")
                    .style("fill", "none");

                let label_positive = this.glabel
                    .selectAll('posi-circle')
                    .data(graph.nodes_label)
                    .enter()
                    .append("circle")
                    .attr("cy", function (d) {
                        return (y(d.name) + yScale.bandwidth()/2 )
                    })
                    .attr("r", function (d) {
                        return d.dc > 0 ? d.dc * 9 : 0
                    })
                    .attr("cx", this.widthL/2)
                    .style("fill", "#c4e6cb")
                    .style("opacity", 1)

                let label_negative = this.glabel
                    .selectAll('nega-circle')
                    .data(graph.nodes_label)
                    .enter()
                    .append("circle")
                    .attr("cy", function (d) {
                        return (y(d.name)  + yScale.bandwidth()/2)
                    })
                    .attr("r", function (d) {
                        return d.dc < 0 ? -d.dc * 9 : 0
                    })
                    .attr("cx", this.widthL/2)
                    .style("fill", "#f5c6cb")
                    .style("opacity", 1)

                // add labels
                let labels = this.glabel
                    .selectAll("labels")
                    .data(graph.nodes_label)
                    .enter()
                    .append("text")
                    .attr("x", this.widthL/2)
                    .attr("y", 5 )
                    .text(function (d) {
                        return (d.name)
                    })
                    .style("text-anchor", function (d) {
                        return d.dc > 0 ? 'end' : d.dc < 0 ? 'start' : 'middle'
                    })
                    .attr("transform", function (d) {
                        return ("translate(" + (d.dc > 0? -10 : 10) + "," + (y(d.name) + yScale.bandwidth()/2) + ")")
                    })
                    .style("font-size", 15)
                    .style('opacity', 1)


                // ====================================================
                //                 all the interactions
                // ====================================================

                function onClickSuper(elemData) {
                    let nodesToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    barsClosed
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    closedValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSobol
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (nodesToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }

                        })

                    sobolValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (nodesToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSuper
                        .style('opacity', function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    superValue
                        .style("opacity", function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    linkLeft
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[0]
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[0]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkRight
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[1]
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[1]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : "#e6e6e6"
                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20: 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : color[0];
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                        })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                }

                function onMouseoverSuper(elemData) {
                    let nodesToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    closedValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0
                        })

                    sobolValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0
                        })

                    superValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.clicked === true || n.active === true ? 1 : 0;
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : "#e6e6e6"
                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : color[0];
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                        })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })


                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                }

                function onReleaseSuper() {
                    barsClosed.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    closedValue.style('opacity', 0)
                    barsSobol.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    sobolValue.style('opacity', 0)
                    barsSuper.style('opacity', function (n) {
                        n.clicked = false;
                        n.active = false;
                        return 1
                    })
                    superValue.style('opacity', 0)
                    linkLeft.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[0]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkRight.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[1]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkTotal.style('stroke',color_links[2]).style('stroke-opacity', 0.1)
                    labels.style("font-size", 15).style("fill",'#111').style('opacity', 1)
                    .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2) + ")")
                    })
                    label_positive.style("opacity", function (label_d) {return label_d.dc > 0 ? 1: 0})
                    label_negative.style("opacity", function (label_d) {return label_d.dc < 0 ? 1: 0})
                    drawArcTotal.innerRadius(arcWidth*3+arcPad).outerRadius(arcWidth*4)
                    drawArcClosed.innerRadius(arcWidth*2+arcPad).outerRadius(arcWidth*3)
                    drawArcSobol.innerRadius(arcWidth+arcPad).outerRadius(arcWidth*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(arcWidth)
                    arcsTotal.attr("d", drawArcTotal).style("opacity", 1)
                    arcsClosed.attr("d", drawArcClosed).style("opacity", 1)
                    arcsSobol.attr("d", drawArcSobol).style("opacity", 1)
                    arcsSuper.attr("d", drawArcSuper).style("opacity", 1)
                    arcsbg.attr("r", arcWidth*4).style("opacity", 1)
                }

                function onClickClosed(elemData) {
                    let nodesToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    barsClosed
                        .style('opacity', function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    closedValue
                        .style("opacity", function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSobol
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (nodesToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    sobolValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (nodesToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSuper
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    superValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    linkLeft
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[0]
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[0]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkRight
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[1]
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[1]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.target.target === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : "#e6e6e6"

                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10

                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : color[1];
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                        })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                }

                function onMouseoverClosed(elemData) {
                    let nodesToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    closedValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.clicked === true || n.active === true ? 1 : 0
                        })

                    sobolValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0
                        })

                    superValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0;
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : "#e6e6e6"

                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : color[1];
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                        })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                }

                function onReleaseClosed() {
                    barsClosed.style('opacity', function (n) {
                        n.clicked = false;
                        n.active = false;
                        return 1
                    })
                    closedValue.style('opacity', 0)
                    barsSobol.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    sobolValue.style('opacity', 0)
                    barsSuper.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    superValue.style('opacity', 0)
                    linkLeft.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[0]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkRight.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[1]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkTotal.style('stroke',color_links[2]).style('stroke-opacity', 0.1)
                    labels.style("font-size", 15).style("fill",'#111').style('opacity', 1)
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2) + ")")
                    })
                    label_positive.style("opacity", function (label_d) {return label_d.dc > 0 ? 1: 0})
                    label_negative.style("opacity", function (label_d) {return label_d.dc < 0 ? 1: 0})
                    drawArcTotal.innerRadius(arcWidth*3+arcPad).outerRadius(arcWidth*4)
                    drawArcClosed.innerRadius(arcWidth*2+arcPad).outerRadius(arcWidth*3)
                    drawArcSobol.innerRadius(arcWidth+arcPad).outerRadius(arcWidth*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(arcWidth)
                    arcsTotal.attr("d", drawArcTotal).style("opacity", 1)
                    arcsClosed.attr("d", drawArcClosed).style("opacity", 1)
                    arcsSobol.attr("d", drawArcSobol).style("opacity", 1)
                    arcsSuper.attr("d", drawArcSuper).style("opacity", 1)
                    arcsbg.attr("r", arcWidth*4).style("opacity", 1)
                }

                function onClickSobol(elemData) {
                    let nodesToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    barsClosed
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (closedToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    closedValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (closedToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSobol
                        .style('opacity', function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0.2
                            }

                        })

                    sobolValue
                        .style("opacity", function (n) {
                            if (n.clicked === true) {
                                return 1
                            }
                            else if (n.name === elemData.id && n.clicked === false) {
                                n.clicked = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    barsSuper
                        .style('opacity', function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (superToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0.2
                            }
                        })

                    superValue
                        .style("opacity", function (n) {
                            if (n.active === true) {
                                return 1
                            }
                            else if (superToHighlight.indexOf(n.id) >= 0 && n.active === false) {
                                n.active = true
                                return 1
                            }
                            else {
                                return 0
                            }
                        })

                    linkLeft
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[3]
                            }
                            else if (link_d.source.source === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[3]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.source.source === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkRight
                        .style('stroke', function (link_d) {
                            if (link_d.active === true) {
                                return color_links[3]
                            }
                            else if (link_d.source.source === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return color_links[3]
                            }
                            else {
                                return "#555"
                            }
                        })
                        .style('stroke-opacity', function (link_d) {
                            if (link_d.active === true) {
                                return 0.5
                            }
                            else if (link_d.source.source === elemData.id && link_d.active === false) {
                                link_d.active = true
                                return 0.5
                            }
                            else {
                                return 0.005
                            }
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : "#e6e6e6"

                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : superToHighlight.indexOf(label_d.name) >= 0 ? color[1] : closedToHighlight.indexOf(label_d.name) >= 0 ? color[0] : "#111"; 
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                         })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                }

                function onMouseoverSobol(elemData) {
                    let nodesToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    closedValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0
                        })

                    sobolValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.clicked === true || n.active === true ? 1 : 0
                        })

                    superValue
                        .style("opacity", function (n) {
                            return n.name === elemData.id || n.active === true || n.clicked === true ? 1 : 0;
                        })

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : "#e6e6e6"

                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id ? '#555' : superToHighlight.indexOf(label_d.name) >= 0 ? color[1] : closedToHighlight.indexOf(label_d.name) >= 0 ? color[0] : "#111";
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                         })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? .3 : 0
                        })
                }

                function onReleaseSobol(elemData) {
                    barsClosed.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    closedValue.style('opacity', 0)
                    barsSobol.style('opacity', function (n) {
                        n.clicked = false;
                        n.active = false;
                        return 1
                    })
                    sobolValue.style('opacity', 0)
                    barsSuper.style('opacity', function (n) {
                        n.active = false;
                        n.clicked = false;
                        return 1
                    })
                    superValue.style('opacity', 0)
                    linkLeft.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[0]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkRight.style('stroke', function(link_d) {
                        link_d.active = false;
                        return color_links[1]
                    }).style('stroke-opacity', function (link_d) {
                        link_d.active = false;
                        return 0.2
                    })
                    linkTotal.style('stroke',color_links[2]).style('stroke-opacity', 0.1)
                    labels.style("font-size", 15).style("fill",'#111').style('opacity', 1)
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2) + ")")
                        })

                    label_positive.style("opacity", function (label_d) {return label_d.dc > 0 ? 1: 0})
                    label_negative.style("opacity", function (label_d) {return label_d.dc < 0 ? 1: 0})
                    drawArcTotal.innerRadius(arcWidth*3+arcPad).outerRadius(arcWidth*4)
                    drawArcClosed.innerRadius(arcWidth*2+arcPad).outerRadius(arcWidth*3)
                    drawArcSobol.innerRadius(arcWidth+arcPad).outerRadius(arcWidth*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(arcWidth)
                    arcsTotal.attr("d", drawArcTotal).style("opacity", 1)
                    arcsClosed.attr("d", drawArcClosed).style("opacity", 1)
                    arcsSobol.attr("d", drawArcSobol).style("opacity", 1)
                    arcsSuper.attr("d", drawArcSuper).style("opacity", 1)
                    arcsbg.attr("r", arcWidth*4).style("opacity", 1)
                }

                function onMouseoverTotal(elemData) {
                    let nodesToHighlight = graph.total_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : e.target === elemData.id ? e.source : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let superToHighlight = graph.super_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    let closedToHighlight = graph.closed_links
                        .map(function (e) {
                            return e.source === elemData.id ? e.target : 0
                        })
                        .filter((value, index, self) => {
                            return self.indexOf(value) === index
                        });

                    linkTotal
                        .style("stroke", function (link_d) {
                            return link_d.source.source === elemData.id && link_d.target.target === elemData.id? color_links[3] : superToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[1] : closedToHighlight.indexOf(link_d.source.source) >= 0 ? color_links[0] : "#dddddd"
                        })
                        .style("stroke-opacity", function (link_d) {
                            return link_d.target.target === elemData.id ? 0.5 : 0.005
                        })

                    labels
                        .style("font-size", function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 20 : 10
                        })
                        .style("fill", function (label_d) {
                            return label_d.name === elemData.id && label_d.name === elemData.id? color[3] : label_d.name === elemData.id ? '#555' : superToHighlight.indexOf(label_d.name) >= 0 ? color[1] : closedToHighlight.indexOf(label_d.name) >= 0 ? color[0] : color[2];
                        })
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2 + 2) + ")")
                        })
                        .style('opacity', function (label_d) {
                            return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                        })

                    label_positive.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })

                    label_negative.style("opacity", function (label_d) {
                        return nodesToHighlight.indexOf(label_d.name) >= 0 ? 1: 0
                    })


                    let othereffect = elemData.total - elemData.ssuper + elemData.sobol - elemData.closed;

                    let tooltipinfo =
                        "total indices: ".fontcolor(color[2]) + elemData.total.toFixed(4) + "<br/>" +
                        "closed indices: ".fontcolor(color[1]) + elemData.closed.toFixed(4) + "<br/>" +
                        "sobol indices: ".fontcolor(color[3]) + elemData.sobol.toFixed(4) + "<br/>" +
                        "super indices: ".fontcolor(color[0]) + elemData.ssuper.toFixed(4) + "<br/>" +
                        "other effect: ".fontcolor("grey") + othereffect.toFixed(4) + "<br/>"

                    d3.select("#tooltip")
                        .style("visibility", 'visible')
                        .style("border", 'none')
                        .style("text-align", 'right')
                        .style("text-justify", 'inter-word')
                        .style("display", 'inter-block')
                        .html(tooltipinfo)

                    drawArcTotal.innerRadius(5*3+arcPad).outerRadius(5*4)
                    drawArcClosed.innerRadius(5*2+arcPad).outerRadius(5*3)
                    drawArcSobol.innerRadius(5+arcPad).outerRadius(5*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(5)

                    arcsbg
                        .attr("r", function (arc_d) {
                            return arc_d.name === elemData.id ? 5*4 : arcWidth*4
                        })
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })

                    arcsTotal
                        .attr("d", drawArcTotal)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsClosed
                        .attr("d", drawArcClosed)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSobol
                        .attr("d", drawArcSobol)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                    arcsSuper
                        .attr("d", drawArcSuper)
                        .style("opacity", function (arc_d) {
                            return arc_d.name === elemData.id ? 1 : 0
                        })
                }

                function onMouseoutTotal() {
                    linkTotal.style('stroke',color_links[2]).style('stroke-opacity', 0.1)
                    labels.style("font-size", 15).style("fill",'#111').style('opacity', 1)
                        .attr("transform", function (label_d) {
                        return ("translate(" + (label_d.dc > 0? -10 : 10) + "," + (y(label_d.name) + yScale.bandwidth()/2) + ")")
                         })
                    label_positive.style("opacity", function (label_d) {return label_d.dc > 0 ? 1: 0})
                    label_negative.style("opacity", function (label_d) {return label_d.dc < 0 ? 1: 0})
                    drawArcTotal.innerRadius(arcWidth*3+arcPad).outerRadius(arcWidth*4)
                    drawArcClosed.innerRadius(arcWidth*2+arcPad).outerRadius(arcWidth*3)
                    drawArcSobol.innerRadius(arcWidth+arcPad).outerRadius(arcWidth*2)
                    drawArcSuper.innerRadius(arcPad).outerRadius(arcWidth)
                    arcsTotal.attr("d", drawArcTotal).style("opacity", 1)
                    arcsClosed.attr("d", drawArcClosed).style("opacity", 1)
                    arcsSobol.attr("d", drawArcSobol).style("opacity", 1)
                    arcsSuper.attr("d", drawArcSuper).style("opacity", 1)
                    arcsbg.attr("r", arcWidth*4).style("opacity", 1 )
                    d3.select('#tooltip').style("visibility", "hidden")
                }


            },
        },


        created() {
            this.N = this.variableList.length;
            this.getNodes(this.N);
            this.getClosedLinks(this.N);
            this.getSuperLinks(this.N);
            this.getTotalLinks(this.N)
        }
    }
</script>

<style scoped>
    div {
        background-color: white;
        margin-top: 0px;
    }

    .title {
        padding-top: 5px;
        padding-bottom: 5px;
        padding-left: 0px;
        margin-left: 0px;
    }

    /* h6 {
        margin-bottom: 0px;
        font-size: 20px;
    } */

    hr {
        margin-top: 1px;
        width: 99%;
        margin-bottom: 10px;
    }

    p {
        color: grey;
    }

    .relation-view-container {
        padding-top: 0px;
        padding-bottom: 0px;
        margin-left: 0px;
        margin-right: 0px;
    }

    .indices-container {
        padding-left: 0px;
        padding-right: 0px;
    }

    .main-cols {
        margin-left: 0px;
        margin-right: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .button {
        margin-left: 0px;
        margin-right: 0px;
        margin-bottom: 0px;
        padding-left: 0px;
        padding-right: 0px;
        text-align: center;
    }

    .button-super {
        margin-top: 15px;
        margin-left: 0px;
        margin-right: 0px;
        padding-top: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .button-sobol {
        margin-top: 15px;
        margin-left: 0px;
        margin-right: 0px;
        padding-top: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .button-closed {
        margin-top: 15px;
        margin-left: 0px;
        margin-right: 0px;
        padding-top: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .button-total {
        margin-top: 15px;
        margin-left: 0px;
        margin-right: 0px;
        padding-top: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .button-label {
        margin-top: 15px;
        margin-left: 0px;
        margin-right: 0px;
        padding-top: 0px;
        padding-left: 0px;
        padding-right: 0px;
    }

    .main-svg {
        margin-top: 0px;
        margin-left: 0px;
        margin-right: 0px;
    }

    .label-container {
        padding-left: 0px;
        padding-right: 0px;
    }

    .main-label {
        margin-top: 0px;
        margin-left: 0px;
        margin-right: 0px;
    }

    .btn-sm, .btn-group-sm > .btn {
        font-size: 20px !important;
    }

    path[Attributes]  {
        border-left-width: thin;
    }

</style>
