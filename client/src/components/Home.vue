<template>
    <div id="home-main-view">
        <!--<Header/>-->
        <b-container class="bv-example-row" fluid>
            <b-row class="home-row">
                <b-col cols="1" class="home-col-left">
                    <div id="title">
                        <h4><b>&lceil;  SenVis  &rfloor;</b></h4>
                        <hr/>
                    </div>
                    <div class="step11">
                        <p class="step"><em> &#10122; Choose a model or upload your own model: </em></p>
                        <b-dropdown id="dropdown-left" variant="info" size="sm" text="S" class="m-2">
                            <template v-slot:button-content>
                                Predefined Model
                            </template>
                            <b-form-group class="form-group">
                                <b-form-radio v-model="selectedModel" :value="currentCase[0]">wind turbine wake - [4 variables]</b-form-radio>
                                <b-form-radio v-model="selectedModel" :value="currentCase[1]">OTL circuit model - [6 variables]</b-form-radio>
                                <b-form-radio v-model="selectedModel" :value="currentCase[2]">piston - [7 variables]</b-form-radio>
                                <b-form-radio v-model="selectedModel" :value="currentCase[3]">ebola spread - [8 variables]</b-form-radio>
                                <b-form-radio v-model="selectedModel" :value="currentCase[4]">wing weight - [10 variables]</b-form-radio>
                                <b-form-radio v-model="selectedModel" :value="currentCase[5]">welch 1992 - [20 variables]</b-form-radio>
                            </b-form-group>
                        </b-dropdown>
                        <b-button size="sm" variant="outline-info" class="my-1 mr-sm-2" type="submit" @click="visualizeModel()">
                            <em>Visualize Predefined Model</em>
                        </b-button>
                    </div>
                    <div class="step12">
                        <b-form-file class="mr-sm-2" ref="file" type="file" v-model="files"
                                     @change="handleFileUpload"
                                     placeholder="Upload ..." size="sm"></b-form-file>

                        
                        <b-button size="sm" variant="outline-light" class="my-1 mr-sm-2" type="submit" @click="visualizeUploadModel()">
                            <em>Visualize Uploaded Model</em>
                        </b-button>
                        <b-button class="button1" variant="dark" v-b-modal.modal-1>See an example</b-button>
                        <b-modal size="lg" id="modal-1" title="A four variable function example:">
                            <pre>
import numpy as np

def get_model(): # keep the name of function unchanged

    # define your function (MUST HAVE)
    def function(Xs):
        C_T = Xs[:, 0]
        kwake = Xs[:, 1]
        d0 = Xs[:, 2]
        x = Xs[:, 3]
        return (1 - np.sqrt(1 - C_T)) / (1 + 2*kwake*x/d0)**2

    # define the name and range of variables (MUST HAVE)
    axes = [dict(name='C_T', domain=(0.4, 0.8)),
            dict(name='k_{wake}', domain=(0.1, 0.2)),
            dict(name='d_0', domain=(1, 80)),
            dict(name='x', domain=(1, 200))]

    return function, axes
                            </pre>
                        </b-modal>
                    </div>
                    <hr/>
                    <div class="step2">
                        <p class="step"><em> &#10123; Select variables of interest for analysis: </em></p>
                        <b-dropdown id="dropdown-1" variant="warning" size="sm" text="S" class="m-2">
                            <template v-slot:button-content>
                                Select Variables
                            </template>
                            <b-form-group>
                                <b-form-checkbox v-model="selected"
                                                v-for="variableName in variableNames"
                                                :key="variableName.index"
                                                :value="variableName.id">
                                    <b>[{{variableName.index}}]</b> &nbsp;&nbsp; {{variableName.name}}
                                <!--<b>[{{variableName.index}}]</b> &nbsp;&nbsp; {{ variableName.name }}-->
                                </b-form-checkbox>
                            </b-form-group>
                        </b-dropdown>
                    </div>
                    <hr/>
                    <!-- <div class="step3">
                        <p><em> &#8594; Switch between the two analytical views:</em></p>
                        <b-form-group>
                            <b-form-radio v-model="selectedView" plain name="some-radios" size="sm" value="A">Relation View</b-form-radio>
                            <b-form-radio v-model="selectedView" plain name="some-radios" size="sm" value="B">Relative View</b-form-radio>
                        </b-form-group>
                    </div> -->
                    <div class="mb-2">
                        <img class="image-name" src="../images/sobol.png" alt="sobol">
                        <img src="../images/s12.png" alt="s12">
                        <br>
                        <img class="image-name" src="../images/closed.png" alt="closed">
                        <img src="../images/sc12.png" alt="s12">
                        <br>
                        <img class="image-name" src="../images/super.png" alt="super">
                        <img src="../images/ss12.png" alt="s12">
                        <br>
                        <img class="image-name" src="../images/total.png" alt="total">
                        <img src="../images/st12.png" alt="s12">   
                    </div>
                    
                </b-col>
                <b-col cols="3" class="home-col-middle">
                    <InfoView v-if="isLoaded" :variableList="variableListIni" :fields="fields" :items="itemsIni"/>
                    <ScatterView v-if="isLoadedVis" :variableList="variableList" :relativeList="relativeList" :items="items" :N="N" :input="inputVariables"/>
                </b-col>
                <b-col cols="8" class="home-col-right">
                    <RelationView v-if="isLoadedVis" :variableList="variableList" :items="items" :input="inputVariables"/>
                    
                </b-col>
                

            </b-row>
        </b-container>

    </div>

</template>


<script>

    import InfoView from './InfoView'
    import RelationView from './RelationView'
    import ScatterView from './ScatterView'
    import axios from 'axios'


    export default {
        name: 'Home',
        components: {
            InfoView,
            RelationView,
            ScatterView
        },
        data () {
            return {
                currentCase: ['wind_turbine_wake', 'otl_circuit', 'piston', 'ebola_spread', 'wing_weight', 'welch_1992'],
                thiscase:[],
                selected: [],
                selectedOrder: null,
                inicase: ['wind_turbine_wake'],
                selectedModel: [],
                inputVariables: [],
                files: null,
                N: 4,
                od: 4,
                self_order: null,
                variableNames: [],
                itemsIni: [],
                variableListIni: [],
                items: [],
                variableList: [],
                relativeList: [],
                fields: [
                    {
                        key: 'var',
                        sortable: true
                    },
                    {
                        key: 'sobol_indices',
                        sortable: true
                    },
                    {
                        key: 'closed_indices',
                        sortable: true
                    },
                    {
                        key: 'total_indices',
                        sortable: true
                    },
                    {
                        key: 'super_indices',
                        sortable: true
                        // variant: 'info'
                    }
                ]
            }
        },
        watch: {
            selected: function (newData) {
                this.inputVariables = newData.map(x => x+1);
                this.inputVariables.sort(function (a, b) {
                    return a - b;
                });
            },
            selectedModel: function (newData) {
                if (newData.length !== 0) this.selectModel(newData)
            }
        },
        methods: {
            ///////  pre-load model - from the model list  \\\\\\\\
            combinationsListAuto() {
                let that = this;
                that.selected= [];
                let data = JSON.stringify({
                    'currentcase': that.inicase[0],
                    'variables': this.inputVariables
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/combinations';
                axios.post(path, data, {headers: {'Content-Type': 'application/json'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let listCom = res['sets']; // res.data['sets'] when removing the above .then line
                        let name = res['name'];

                        that.variableNames = [];
                        let tem_name = {};
                        for (let i = 0; i < name.length; i++ ) {
                            let vvid = "v_" + (i+1).toString()
                            tem_name = {
                                "id": i,
                                "index": vvid,
                                "name": name[i]//"[" + " " + vvid + " " + "] " + " " + name[i],
                            }

                            that.variableNames[i] = tem_name
                        }
                        let nn = res['order'];
                        let vlist = [];
                        for (let i = 0; i < nn ; i++) {
                            vlist[i] = listCom[0][i+1];
                        }
                        that.variableListIni = vlist;

                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            getSingleIndicesAuto() {
                let self = this;
                let data = JSON.stringify({
                    'currentcase': self.inicase[0],
                    'variables': this.inputVariables
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/sense';
                axios.post(path, data, {headers: {'Content-Type': 'application/json'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let nn = res['order'];
                        let data = res['nodes']; // res.data['nodes'] when removing the above .then line
                        self.od = res['od'];
                        self.inputorder = res['chosenorder'];
                        let listRela = res['relatives'];
                        let indices = [];
                        let relativevalue = [];
                        for (let i = 0; i < self.od; i++) {
                            indices[i] = data[0][i+1];
                            relativevalue[i] = listRela[0][i+1]
                        }
                        console.log(indices, relativevalue);
                        self.itemsIni = indices;
                        self.relativeList = relativevalue;
                        self.N = nn;//self.inputorder;

                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },

            ///////  pre-display infoview  \\\\\\\\\
            preCombinationsList(this_case) {
                let that = this;
                that.selected= [];

                let data = JSON.stringify({
                    'currentcase': this_case
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/precom';
                axios.post(path, data, {headers: {'Content-Type': 'application/json','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let listCom = res['sets']; // res.data['sets'] when removing the above .then line
                        let name = res['name'];

                        that.variableNames = [];
                        let tem_name = {};
                        for (let i = 0; i < name.length; i++ ) {
                            let vvid = "v_" + (i+1).toString()
                            tem_name = {
                                "id": i,
                                "index": vvid,
                                "name": name[i] // "[" + " " + vvid + " " + "] " + " " + name[i],
                            }
                            that.variableNames[i] = tem_name
                        }
                        let nn = res['order'];
                        let vlist = [];
                        for (let i = 0; i < nn ; i++) {
                            vlist[i] = listCom[0][i+1];
                        }
                        that.variableListIni = vlist;
                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            preGetSingleIndices(this_case) {
                let start_time = new Date().getTime();
                let self = this;

                let data = JSON.stringify({
                    'currentcase': this_case
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/presense';
                axios.post(path, data, {headers: {'Content-Type': 'application/json','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let nn = res['order'];
                        let data = res['nodes']; // res.data['nodes'] when removing the above .then line
                        self.od = res['od'];
                        let indices = [];
                        for (let i = 0; i < self.od; i++) {
                            indices[i] = data[0][i+1];
                        }
                        self.itemsIni = indices;
                        self.N = nn;
                        console.log('Time elapsed:', new Date().getTime() - start_time);

                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            selectModel: function (this_case) {
                this.thiscase = this_case;
                this.variableList = [];
                this.items = [];
                this.N = null;
                this.preCombinationsList(this_case);
                this.preGetSingleIndices(this_case);
                this.files = null
            },

            ///////  for select model - model from file  \\\\\\\
            combinationsList() {
                let that = this;
                let data = JSON.stringify({
                    'currentcase': this.thiscase,
                    'variables': this.inputVariables
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/combinations';
                axios.post(path, data, {headers: {'Content-Type': 'application/json'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let listCom = res['sets']; // res.data['sets'] when removing the above .then line
                        let name = res['name'];

                        that.variableNames = [];
                        let tem_name = {};
                        for (let i = 0; i < name.length; i++ ) {
                            let vvid = "v_" + (i+1).toString()
                            tem_name = {
                                "id": i,
                                "index": vvid,
                                "name": name[i]//"[" + " " + vvid + " " + "] " + " " + name[i],
                            }

                            that.variableNames[i] = tem_name
                        }
                        let nn = res['order'];
                        // console.log(listCom);
                        let vlist = [];
                        for (let i = 0; i < nn ; i++) {
                            vlist[i] = listCom[0][i+1];
                        }
                        that.variableList = vlist;

                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            getSingleIndices() {
                let start_time = new Date().getTime();
                let self = this;

                let data = JSON.stringify({
                    'currentcase': this.thiscase,
                    'variables': this.inputVariables
                });
                // ================== old way ==============
                const path = 'http://127.0.0.1:5000/sense';
                axios.post(path, data, {headers: {'Content-Type': 'application/json'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then((res) => {
                        let nn = res['order'];
                        let data = res['nodes']; // res.data['nodes'] when removing the above .then line
                        self.od = res['od'];
                        self.inputorder = res['chosenorder'];
                        let listRela = res['relatives'];
                        let indices = [];
                        let relativevalue = [];
                        for (let i = 0; i < self.od; i++) {
                            indices[i] = data[0][i+1];
                            relativevalue[i] = listRela[0][i+1]
                        }
                        self.items = indices;
                        self.relativeList = relativevalue;
                        self.N = nn;//self.inputorder;

                        console.log('Time elapsed:', new Date().getTime() - start_time);

                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            visualizeModel() {
                this.combinationsList()
                this.getSingleIndices()
                this.files = null
            },

            ///////  for uploading model  \\\\\\\
            preModelCombinationList(file) {
                let that = this;
                let formData = new FormData();
                formData.append('file', file);
                let path = 'http://127.0.0.1:5000/premodelcom'; // premodelcom
                if (file['name'] === "fire_spread.py")
                    path = 'http://127.0.0.1:5000/prefirecom'; // premodelcomv
                axios.post(path, formData, {headers: {'Content-Type': 'multipart/form-data','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then(res => {
                        console.log(res);
                        let listCom = res['sets']; // res.dat
                        let name = res['name'];

                        that.variableNames = [];
                        let tem_name = {};
                        for (let i = 0; i < name.length; i++ ) {
                            let vvid = "v_" + (i+1).toString();
                            tem_name = {
                                "id": i,
                                "index": vvid,
                                "name": name[i]// "[" + " " + vvid + " " + "] " + " " + name[i],
                            }
                            that.variableNames[i] = tem_name
                        }
                        let nn = res['order'];
                        let vlist = [];
                        for (let i = 0; i < nn ; i++) {
                            vlist[i] = listCom[0][i+1];
                        }
                        that.variableListIni = vlist;
                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            preModelIndices(file) {
                let self = this;
                let formData = new FormData();
                formData.append('file', file);
                let path = 'http://127.0.0.1:5000/premodelsense'; //
                if (file['name'] === "fire_spread.py")
                    path = 'http://127.0.0.1:5000/prefiresense';
                axios.post(path, formData, {headers: {'Content-Type': 'multipart/form-data','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then(res => {

                        let nn = res['order'];
                        let data = res['nodes']; // res.data['nodes'] when removing the above
                        self.od = res['od'];
                        let indices = [];
                        for (let i = 0; i < self.od; i++) {
                            indices[i] = data[0][i+1];

                        }
                        self.itemsIni = indices;
                        self.N = nn;
                    })
                    .catch((error) => {
                        console.error(error)
                    })

            },
            handleFileUpload(e) {
                let self = this
                self.files = null
                self.selected = [];
                self.selectedModel = [];
                self.variableList = [];
                self.items = [];
                self.N = null;

                let file = e.target.files || e.dataTransfer.files;
                if (!file.length)
                    return;
                self.files = file[0]
                this.preModelCombinationList(self.files);
                this.preModelIndices(self.files);
            },

            modelCombinationList() {
                let that = this;
                let formData = new FormData();
                formData.append('file',  that.files);
                formData.append('json', JSON.stringify({'variables': that.inputVariables}))
                let path = 'http://127.0.0.1:5000/modelcom';
                if (that.files['name'] === "fire_spread.py")
                    path = 'http://127.0.0.1:5000/firecom';
                axios.post(path, formData, {headers: {'Content-Type': 'multipart/form-data','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then(res => {
                        let listCom = res['sets']; // res.data['sets'] when removing the above .then line
                        let name = res['name'];

                        that.variableNames = [];
                        let tem_name = {};
                        for (let i = 0; i < name.length; i++ ) {
                            let vvid = "v_" + (i+1).toString()
                            tem_name = {
                                "id": i,
                                "index": vvid,
                                "name": name[i]//"[" + " " + vvid + " " + "] " + " " + name[i],
                            }
                            that.variableNames[i] = tem_name
                        }
                        let nn = res['order'];
                        let vlist = [];
                        for (let i = 0; i < nn ; i++) {
                            vlist[i] = listCom[0][i+1];
                        }
                        that.variableList = vlist;
                    })
                    .catch((error) => {
                        console.error(error)
                    })
            },
            modelIndices() {
                let self = this;
                let formData = new FormData();
                formData.append('file',  self.files);
                formData.append('json', JSON.stringify({'variables': self.inputVariables}))
                let path = 'http://127.0.0.1:5000/modelsense';
                if (self.files['name'] === "fire_spread.py")
                    path = 'http://127.0.0.1:5000/firesense';
                axios.post(path, formData, {headers: {'Content-Type': 'multipart/form-data','Access-Control-Allow-Origin': '*'}})
                    .then(res => JSON.parse(JSON.stringify(res.data)))
                    .then(res => {

                        let nn = res['order'];
                        let data = res['nodes']; // res.data['nodes'] when removing the above .then line
                        self.od = res['od'];
                        self.inputorder = res['chosenorder'];
                        let listRela = res['relatives'];
                        let indices = [];
                        let relativevalue = [];
                        for (let i = 0; i < self.od; i++) {
                            indices[i] = data[0][i+1];
                            relativevalue[i] = listRela[0][i+1]
                        }
                        self.items = indices;
                        self.relativeList = relativevalue;
                        self.N = nn;

                    })
                    .catch((error) => {
                        console.error(error)
                    })

            },
            visualizeUploadModel() {
                this.modelCombinationList()
                this.modelIndices()
            }

        },
        created() {
            this.inputVariables = [];
            this.inputorder = this.N;
        },
        computed:{
            isLoaded() {
                if (this.itemsIni.length !== 0)
                    return (this.itemsIni[0]['sobol'].length === this.N ) && (this.variableListIni[0].length === this.N );
            },
            isLoadedVis() {
                console.log(this.relativeList, this.items, this.inputVariables)
                if (this.items.length !== 0)
                    return (this.items[0]['sobol'].length === this.inputorder ) && (this.variableList[0].length === this.inputorder  ) && (this.relativeList[0].length === this.inputorder);
                else return false

            },
        }

    }
</script>

<style>
    body {
        font-size: 18px;
    }
</style>

<style lang="scss" scoped>
    p {
        margin-left: 5px;
        margin-bottom: 10px;
        text-align: left;
        color:white;
    }

    .guide {
        color: grey;
    }

    h4 {
        margin-top: 60px;
        margin-bottom: 60px;
        color:white;
        text-align: center;
        
    }

    h6 {
        margin-bottom: 10px;
        color: white;
    }

    .step11 {
        margin-top: 10px;
        margin-bottom: 30px;
    }

    .step12 {
        margin-top: 20px;
        margin-bottom: 40px;
    }

    .step2 {
        margin-top: 10px;
        margin-bottom: 50px;
    }

    .navbar-brand {
        font-size: 1.2rem;
    }

    hr {
        display: block;
        height: 1px;
        border: 0;
        border-top: 1px solid grey;
        margin: 1em 0;
        padding: 0;
    }


    #navbarcustom {
        padding-top: 3px !important;
        padding-bottom: 3px !important;
    }

    .my-1 {
        margin-right: 8px
    }

    .home-col-left {
        padding-left: 0px;
        padding-right: 0px;
        background-color: #343a40;
    }

    .home-col-middle {
        padding-top: 5px;
        padding-left: 5px;
        padding-right: 0px;
    }

    .home-col-right {
        padding-top: 5px;
        padding-left: 5px;
        padding-right: 5px;
    }

    .dropdown {
        width: 90%; 
    }


    .btn-sm, .btn-group-sm > .btn {
        /*padding-top: 0px;*/
        font-size: 18px !important;
        margin-left: 8px;
        text-align: center;
    }

    .b-custom-control-sm.custom-file, .b-custom-control-sm {
        margin-left: 8px;
        margin-bottom: 8px;
        width: 90%;
    }

    .b-custom-control-sm {
        margin-top: 10px;
        margin-left: 10px;
        color: white;
    }

    #home-main-view {
        background-color: white; // #fafafa !important;
    }

    .badge {
        vertical-align: middle;
        font-size: 100%;
        padding-top: 10px;
    }

    img {
        margin-top: 10px;
        margin-left:0px;
        width: 80px;
        height: 70px;
    }

    .image-name {
        margin-left: 12px;
        margin-right: 10px;
        width: 40px;
        height: 40px;
    }

    .button1 {
        margin-left: 12px;
        margin-top: 0px;
        margin-bottom: 0px;
        text-align: center;
    }


</style>

