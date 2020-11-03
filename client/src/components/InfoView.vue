<template>
    <div id="info-view">
        <b-container class="info-view-container">
            <b-card no-body >
                <b-tabs card>
                    <!--always have the first order available-->
                    <b-tab title="1-order" active >
                        <b-card-text >
                            <b-table sticky-header small hover outlined
                                     :items="indices[0]"
                                     :fields="fields">
                                <!-- A custom formatted header cell for field 'name' -->
                                <template v-slot:head(sobol_indices)="data">
                                    <span class="text-danger">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(closed_indices)="data">
                                    <span class="text-success">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(total_indices)="data">
                                    <span class="text-purple">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(super_indices)="data">
                                    <span class="text-info">{{ data.label }}</span>
                                </template>

                            </b-table>
                        </b-card-text>
                    </b-tab>

                    <!-- Render other Tabs, supply a unique `key` to each tab -->
                    <b-tab v-for="i in tabs" :key="'dyn-tab-' + i" :title="i+2 + '-order'">
                        <b-card-text>
                            <b-table sticky-header small hover outlined
                                     :items="indices[i+1]"
                                     :fields="fields">
                                <!-- A custom formatted header cell for field 'name' -->
                                <template v-slot:head(sobol_indices)="data">
                                    <span class="text-danger">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(closed_indices)="data">
                                    <span class="text-success">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(total_indices)="data">
                                    <span class="text-purple">{{ data.label }}</span>
                                </template>
                                <template v-slot:head(super_indices)="data">
                                    <span class="text-info">{{ data.label }}</span>
                                </template>

                            </b-table>
                        </b-card-text>
                        <b-card-footer :i="i">
                            <div>
                                <b-button v-show="tabCounter === i+1" size="sm" variant="danger" class="float-right" @click="closeTab(i)">
                                    Close
                                </b-button>
                            </div>
                        </b-card-footer>


                    </b-tab>

                    <!-- New Tab Button (Using tabs-end slot) -->
                    <template v-slot:tabs-end>
                        <b-nav-item @click.prevent="newTab" href="#"><b v-if="tabCounter !== N - 1">+</b></b-nav-item>
                    </template>

                </b-tabs>
            </b-card>
        </b-container>

    </div>
</template>

<script>
    export default {
        name: 'InfoView',
        props: {
            fields: Array,
            items: Array,
            variableList: Array,
        },
        data() {
            return {
                N: this.variableList.length,
                title: "Information View",
                tabs: [],
                tabCounter: 0,
                indices: [],
                vlist: this.variableList,
                values: this.items
            }
        },
        methods: {
            closeTab(x) {
                for (let i = 0; i < this.tabs.length; i++) {
                    if (this.tabs[i] === x) {
                        this.tabs.splice(i, 1);
                        this.tabCounter -= 1
                    }
                }
            },
            newTab() {
                if (this.tabCounter < this.N -1)
                    this.tabs.push(this.tabCounter++)

            },
            computeItems: function(n) {
                let self = this;
                if (self.values.length !== 0) {
                    console.log(self.values);
                    for (let i = 0; i < n; i++) {
                        self.indices[i] = [];
                        for (let j = 0; j < self.vlist[i].length; j++) {
                            let dc = self.values[i]['dc'][j];
                            let si = self.values[i]['sobol'][j];
                            let sc = self.values[i]['closed'][j];
                            let st = self.values[i]['total'][j];
                            let ss = self.values[i]['super'][j];
                            let vSet = self.vlist[i][j];

                            self.indices[i][j] = {
                                'var': "v_" + vSet.join("_"),
                                "sobol_indices": si,
                                "closed_indices": sc,
                                "total_indices": st,
                                "super_indices": ss,
                                _cellVariants: { "var": dc>0 ? 'success' : dc < 0? 'danger':'' }
                            };
                        }
                    }
                }
                return self.indices;

            }
        },
        mounted: function() {
            this.computeItems(this.N)
        },
        watch: {
            variableList: {
                immediate: true,
                handler() {
                    this.vlist = this.variableList;
                    console.log(this.vlist)

                }
            },
            items: {
                immediate: true,
                handler() {
                    this.values = this.items;
                    this.N = this.items.length;
                    this.indices = []
                    this.indices = this.computeItems(this.N)
                }
            },
            N: function (newData) {
                this.indices = []
                this.indices = this.computeItems(newData)

            }

        },
        created() {
            this.N = this.variableList.length;
            this.indices = this.computeItems(this.N);
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
    div {
        background-color: white;
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

    hr {
        margin-top: 0px;
        width: 99%;
        margin-bottom: 10px;
    }

    .info-view-container {
        padding-top: 1px;
        padding-bottom: 10px;
        padding-left: 0px;
        padding-right: 5px;
        min-height: 460px !important;
    }

    .text-purple {
        color: #a157a6  /*984ea3*/
    }

    .text-closed {
        color: #f4a90e
    }

    p {
        font-size: 18px;
    }

</style>
