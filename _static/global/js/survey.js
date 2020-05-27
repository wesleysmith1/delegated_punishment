let surveyComponent = {
    components: {},
    props: {
        paymentMax: Number,
        tokenChoices: Number,
    },
    data: function () {
        return {
            submitted: false,
            // objects need to have initial values in order for the
            // created hook to initialize their values for some reason
            resultsObj: {1:null,2:null,3:null,4:null,5:null,6:null,7:null,8:null,9:null,10:null},
            willingnessToPay: {1:null,2:null,3:null,4:null,5:null,6:null,7:null,8:null,9:null,10:null},
            inputValues: {1:null,2:null,3:null,4:null,5:null,6:null,7:null,8:null,9:null,10:null}
        }
    },
    created: function() {
        for(let i = 1; i < this.tokenChoices+1; i++) {
            let k = (i).toString()
            this.resultsObj[k] = null;
            this.willingnessToPay[k] = null;
            this.inputValues[k] = null;
        }
    },
    mounted: function () {

    },
    computed: {
    },
    methods: {
        submit: function() {
            this.submitted = true;
            this.$emit('submit-survey', this.mapWTP());
        },
        mapWTP: function() {
            let m = {};
            for(let i = 1; i < this.tokenChoices+1; i++) {
                if (i === 1) {
                    m[i] = {
                        'wtp': this.formatNum(this.resultsObj[i]),
                            'total': this.formatNum(this.resultsObj[i]) }
                } else {
                    let wtp = null
                    if (this.formatNum(this.resultsObj[i-1]) !== null && this.formatNum(this.resultsObj[i]) !== null)
                        wtp = this.formatNum(this.resultsObj[i]) - this.formatNum(this.resultsObj[i-1])
                    let total = this.formatNum(this.resultsObj[i])
                    m[i] = {
                        'wtp': wtp,
                            'total': total} }

            }
           return m
        },
        formatNum: function(n) {
            return n
        },
        updateResults: function(i) {
            this.resultsObj[i] = this.inputValues[i];
            this.clearInputAt(i);
        },
        incrementInput: function(i) {
            this.clearInputAt(i);
            this.resultsObj[i]++;
        },
        decrementInput: function(i){
            this.clearInputAt(i);
            this.resultsObj[i]--;
        },
        clearInputAt: function(i) {
            // clear value
            this.$refs['surveyinput' + i][0].value = null;

            this.inputValues[i] = null;
        },
        isNumber: function(evt) {
            evt = (evt) ? evt : window.evt;
            var charCode = (evt.which) ? evt.which : evt.keyCode;
            if ((charCode < 48 || charCode > 57) && charCode !== 45) {
                evt.preventDefault();
            } else {
                return true;
            }
        },
        onEnter: function(i) {
            if (this.showSubmit(i))
                this.updateResults(i)
        },
        showSubmit: function(i) {
            return !(this.inputValues[i] !== 0 && !this.inputValues[i])
        }
    },
    template:
        `
        <div style="margin: auto; width: 50%;">
          
            <div class="item">
               <div>Total number of officer tokens</div>
            
               <div>Maximum you would pay</div>
            </div>
            <hr>
            <div v-for="i in tokenChoices">
                <div class="item" style="display: flex;">
                    <div>{{ i }} <div class="officer-unit" style="display: inline-block; height: 15px; width: 15px; "></div></div>
                    
                    <div style="display: flex;">
                        <button v-show="showSubmit(i)" type="button" class="btn btn-warning" style="position: relative; left: 250px;" @click="updateResults(i)">Update</button>
                        <div class="input-group">
                          <div class="input-group-prepend">
                            <button type="button" class="btn btn-secondary" @click="decrementInput(i)">-</button>
                          </div>
                          <input v-on:keyup.enter="onEnter(i)"  :placeholder="resultsObj[i]" :ref="'surveyinput' + i" v-model.number="inputValues[i]" @keypress="isNumber($event)" type="number" class="form-control" style="width: 100px; text-align: center;">
                          <div class="input-group-append">
                            <button type="button" class="btn btn-secondary" @click="incrementInput(i)">+</button>
                          </div>
                            <!--<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px; position: relative; top: 5px; left: 10px;">-->
                        </div>
                    </div>
            
                </div>
                <hr>
            </div>
        </div>
        `
}
