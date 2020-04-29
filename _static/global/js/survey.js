let surveyComponent = {
    components: {},
    props: {
        paymentMax: Number,
        tokenChoices: Number,
    },
    data: function () {
        return {
            submitted: false,
            resultsObj: {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0},
            willingnessToPay: {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0},
        }
    },
    created: function() {
        for(let i = 1; i < this.tokenChoices+1; i++) {
            this.resultsObj[i] = null;
            this.willingnessToPay[i] = null;
        }
    },
    mounted: function () {

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
                    m[i] = {
                        'wtp': this.formatNum(this.resultsObj[i]) - this.formatNum(this.resultsObj[i-1]),
                            'total': this.formatNum(this.resultsObj[i])} }

            }
           return m
        },
        formatNum: function(n) {
            return n | 0
        }
    },
    template:
        `
        <div style="margin: auto; width: 50%;">
            <div class="item">
               <div>Officer's total # tokens</div>
            
               <div>Your total willingness to pay</div>
            </div>
            <hr>
            <div v-for="i in tokenChoices">
                <div class="item">
                    <div>{{ i }} <div class="officer-unit" style="display: inline-block; height: 15px; width: 15px; "></div></div>
                    
                    <div style="display: flex;">
                        <select v-model="resultsObj[i]" :disabled="submitted" class="form-control form-control-sm">
                            <option value="null" default>--</option>
                            <option>0</option>
                            <option v-for="x in paymentMax">{{ x }}</option>
                        </select>
                        <img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px; position: relative; top: 5px; left: 10px;">
                    </div>
                </div>
                <hr>
            </div>
        </div>
        `
}
