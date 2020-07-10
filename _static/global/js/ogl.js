let oglComponent = {
    components: {},
    props: {
        paymentMax: Number,
        submitted: Boolean,
        provisionalTotals: Object,
        playerId: Number,
        bigN: Number,
        smallN: Number,
        q: Number,
        gamma: Number,
        method: Number,
        omega: Number,
    },
    data: function () {
        return {
            numberTokens: 0,
            paymentOptions: null,
            yourCost: 0,
            provisional: {},
            increased: {},
            decreased: {},
            formInputNum: null,
            increasedTotals: {},
            decreasedTotals: {},
            inputPlaceholder: 0,
        }
    },
    created: function() {
        Decimal.set({ precision: 8 })
        this.paymentOptions = this.paymentMax * 2;

        // this.YourCost = 0;

        this.updateDifferentialTotals();
        //
        this.updateCosts();

    },
    mounted: function () {

    },
    methods: {
        jsonCopy: function(src) {
            return JSON.parse(JSON.stringify(src));
        },
        incrementTotal: function() {
            this.numberTokens += 1
            this.inputPlaceholder = this.numberTokens
            this.inputChange()
        },
        decrementTotal: function() {
            this.numberTokens -= 1
            this.inputPlaceholder = this.numberTokens
            this.inputChange()
        },
        validateOmega: function() {
            return (this.formInputNum < this.omega && this.formInputNum > (-1* this.omega))
        },
        handleFormSubmission: function() {
            if (Number.isInteger(this.formInputNum) && this.validateOmega()) {
                this.updatePlaceholder()

                this.inputChange()
            } else {
                this.formInputNum = null
            }
        },
        updatePlaceholder: function() {
            this.numberTokens = this.formInputNum
            this.inputPlaceholder = this.formInputNum
            this.formInputNum = null;
        },
        cancelTimeout: function() {
            if (this.timeout)
                clearTimeout(this.timeout);
        },
        inputChange: function() {
            this.$emit('update', this.numberTokens);
        },
        arrIntSum: function(arr) {
            if (!arr) {
                console.error('arrIntSum received empty value')
                return -999
            }

            if (!Array.isArray(arr))
                arr = Object.values(arr)

            let sum =  arr.reduce(function(a,b){
                return a + b
            }, 0);
            return Math.round(sum);
        },
        decimalSum: function(arr) {

            if (!arr) {
                console.error('decimalSum function requires input')
                return -664
            }

            let sum = Decimal(0)

            arr = Object.values(arr)

            arr.forEach(function(d) {
                sum = sum.add(d)
            });

            return Math.round(sum);
        },
        calculateThetas: function(zzzzz) {
            let thetaResults = {}
            let total = this.arrIntSum(zzzzz)

            for(const pid in zzzzz) {
                let x = 0;
                let playerId2 = parseInt(pid)

                let tempTotal = total // something here is wrong
                tempTotal -= zzzzz[playerId2]

                for(const pid2 in zzzzz) {
                    let pid2_num = parseInt(pid2)
                    if (pid2 === pid)
                        continue;

                    let ptotal = zzzzz[parseInt(pid2)]

                    let xxx = Decimal(ptotal - Decimal(1 / (this.smallN - 1)) * (tempTotal)) ** 2

                    x += xxx
                }

                thetaResults[parseInt(pid)] = Decimal(Decimal(this.gamma / 2) * Decimal(1 / (this.smallN - 2)) * x);

            }
            return thetaResults;
        },
        calculateOgl: function(zzzzz) {
            // the direction is +- 1.

            let thetas;
            // only ogl has theta. Other gl mechanisms do not
            if (this.method !== 1) { // todo: make this more obvious so we don't forget about it and break something
                let empty = {};
                for (const pid in zzzzz) {
                    empty[parseInt(pid)] = 0;
                }
                thetas = empty;
            } else {
                thetas = this.calculateThetas(zzzzz);
            }

            let oglResults = {};

            let total = this.arrIntSum(zzzzz);

            for(let id in zzzzz) {
                let pid = parseInt(id);

                let ptotal = zzzzz[pid];

                oglResults[pid] = Decimal((this.q / this.bigN) * total + (this.gamma/2) * (this.smallN/(this.smallN-1)) * Math.pow(ptotal - (1/this.smallN) * total, 2)).sub(thetas[pid]);
            }

            return oglResults
        },
        updateDifferentialTotals: function() {
            this.increasedTotals = this.jsonCopy(this.provisionalTotals);
            this.increasedTotals[this.playerId] += 1;
            this.decreasedTotals = this.jsonCopy(this.provisionalTotals);
            this.decreasedTotals[this.playerId] -= 1;
        },
        updateCosts: function() {
            this.provisional = this.calculateOgl(this.provisionalTotals);
            this.increased = this.calculateOgl(this.increasedTotals);
            this.decreased = this.calculateOgl(this.decreasedTotals);
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
    },
    watch: {
        provisionalTotals: function(newVal) {
            if (!newVal) return;

            this.updateDifferentialTotals();

            this.updateCosts()
        },
    },
    computed: {

    },
    template:
        `
      <div>      
        <div class="row" style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="min-width: 200px; display: flex; flex-direction: column; margin-bottom: 16px;">
                <h5 style="text-align: center;"></h5>
                <button v-show="provisionalTotals[playerId] > (-1*omega)" @click="decrementTotal(1)" type="button" class="btn btn-primary">Update tokens (-1)</button>
            </div>
            
            <div>
                <h3 style="text-align: center;">Provisional</h3>
                <form class="form-inline" @submit.prevent="handleFormSubmission()">
                  <button type="submit" class="btn btn-primary" :disabled="!formInputNum">Update tokens</button>
                  <div class="form-group" style="max-width: 250px;">
                    <input type="number" step="1" class="form-control" v-on:keyup.enter="handleFormSubmission()" @keypress="isNumber($event)" :placeholder="inputPlaceholder" style="max-width: 250px;" v-model.number="formInputNum">
                  </div>
                </form>
            </div>
            
            <div style="min-width: 200px; display: flex; flex-direction: column; margin-bottom: 16px;">
                <h5 style="text-align: center;"></h5>
                <button v-show="provisionalTotals[playerId] < omega" @click="incrementTotal(1)" type="button" class="btn btn-primary">Update tokens (+1)</button>
            </div>
        </div>
      
        <div class="row" style="display: flex; justify-content: space-between;">
            <div style="min-width: 200px;">
                <div v-show="provisionalTotals[playerId] > (-1*omega)">
                    <div class="list-group">
                         <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your tokens:</div>
                                <div>{{provisionalTotals[playerId] - 1}}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your cost:</div>
                                <div>{{ decreased[playerId] | integerFilter }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ decimalSum(decreased) | integerFilter }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrIntSum(provisionalTotals) - 1 }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        
        
            <div style="min-width: 350px;">
                <div>
                    <div class="list-group">
                        <div class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div><b>Your Tokens:</b></div>
                                <div><b>{{provisionalTotals[playerId]}}</b></div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div><b>Your cost:</b></div>
                                <div><b>{{ provisional[playerId] | integerFilter }}</b></div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ decimalSum(provisional) | integerFilter }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item list-group-item-primary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrIntSum(provisionalTotals) }}</div>
                            </div>
                        </div>  
                    </div>
                </div>
            </div>
            
            <div style="min-width: 200px;">
                <div v-show="provisionalTotals[playerId] < omega">            
                    <div class="list-group">
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your tokens:</div>
                                <div>{{ provisionalTotals[playerId] + 1 }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your cost:</div>
                                <div>{{ increased[playerId] | integerFilter }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ decimalSum(increased) | integerFilter  }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrIntSum(provisionalTotals) + 1}}</div>
                            </div>
                        </div> 
                    </div> 
                </div>
            </div>
        </div>
      </div>
      `
}
