let oglComponent = {
    components: {},
    props: {
        paymentMax: Number,
        submitted: Boolean,
        provisionalCosts: Object,
        provisionalTotals: Object,
        playerId: Number,
        bigN: Number,
        smallN: Number,
        q: Number,
        gamma: Number,
        method: Number,
    },
    data: function () {
        return {
            location: null,
            numberTokens: 0,
            paymentOptions: null,
            costs: [],
            totals: [],
            yourCost: 0,
            yourTotal: 0,
            calculations: {},
            provisional: {},
            increased: {},
            decreased: {},
            formInputNum: null,
        }
    },
    created: function() {
        this.paymentOptions = this.paymentMax * 2;

        // this.yourTotal = {};
        // this.YourCost = 0;
        // this.totals = Object.values(newVal);
        // this.costs = {};
        //
        this.provisional = this.calculateOgl(0)
        this.increased = this.calculateOgl(1)
        this.decreased = this.calculateOgl(-1)
    },
    mounted: function () {

    },
    methods: {
        incrementTotal: function() {
            this.numberTokens += 1
            this.inputChange()
        },
        decrementTotal: function() {
            this.numberTokens -= 1
            this.inputChange()
        },
        handleFormSubmission: function() {
            if(Number.isInteger(this.formInputNum)) {
                this.numberTokens = this.formInputNum
                this.inputChange()
            } else {
                alert('invalid input')
                this.formInputNum = null
            }
        },
        cancelTimeout: function() {
            if (this.timeout)
                clearTimeout(this.timeout);
        },
        inputChange: function() {
            this.$emit('update', this.numberTokens);
        },
        arrSum: function(arr) {
            if (!Array.isArray(arr)) {
                arr = Object.values(arr)
            }
            return arr.reduce(function(a,b){
                return a + b
            }, 0);
        },
        calculateThetas: function(direction) {
            let thetaResults = {}
            let total = this.arrSum(this.totals) + direction

            if (this.method !== 1) { // todo: make this more obvious so we don't forget about it and break something
                let empty = {}
                let length = this.totals.length
                for (const pid in this.provisionalTotals) {
                    empty[parseInt(pid)] = 0
                }
                return empty
            }

            for(const pid in this.provisionalTotals) {
                let x = 0;
                let playerId2 = parseInt(pid)

                let tempTotal = total // something here is wrong
                tempTotal -= this.provisionalTotals[playerId2]

                for(const pid2 in this.provisionalTotals) {
                    let pid2_num = parseInt(pid2)
                    if (pid2 === pid)
                        continue;

                    let ptotal = this.provisionalTotals[parseInt(pid2)]
                    if (this.playerId === pid2_num) {
                        ptotal += direction
                        console.log(ptotal)
                    }

                    xxx = Math.pow(ptotal - (1 / (this.smallN - 1)) * (tempTotal),2)

                    x += xxx
                }

                console.log('end of theta calculation')

                thetaResults[parseInt(pid)] = (this.gamma / 2) * (1 / (this.smallN - 2)) * x;

            }
            return thetaResults
        },
        calculateOgl: function(direction) {
            // the direction is +- 1.
            let thetas = this.calculateThetas(direction, )
            if (direction === 0)
                console.log('thetas: ', thetas)
            let oglResults = {}

            let total = this.arrSum(this.provisionalTotals) + direction
            console.log('total', total)

            for(let id in this.provisionalTotals) {
                let pid = parseInt(id)

                let ptotal = this.provisionalTotals[pid]
                if (pid === this.playerId) {
                    ptotal += direction
                }

                console.log('ptotal', ptotal, 'total', total)

                oglResults[pid] = (this.q / this.bigN) * total + (this.gamma/2) * (this.smallN/(this.smallN-1)) * Math.pow(ptotal - (1/this.smallN) * total, 2) - thetas[pid]
            }

            // console.log('OGL results ', oglResults)
            return oglResults
        }
    },
    watch: {
        provisionalCosts: function(newVal) {
            this.yourCost = newVal[this.playerId] ? newVal[this.playerId] : -1;
            this.costs = Object.values(newVal);
        },
        provisionalTotals: function(newVal) {
            this.yourTotal = newVal[this.playerId] ? newVal[this.playerId] : -1;
            this.totals = Object.values(newVal);

            this.provisional = this.calculateOgl(0)
            // console.log('local', this.provisional)
            // console.log('server', this.provisionalCosts)
            this.increased = this.calculateOgl(1)
            this.decreased = this.calculateOgl(-1)
        },
    },
    computed: {

    },
    template:
        `
      <div>      
        <div class="row" style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div style="min-width: 200px; display: flex; flex-direction: column; margin-bottom: 16px;">
                <h5 style="text-align: center;">Deviation</h5>
                <div style="text-align: center;">
                    <button @click="decrementTotal(1)" type="button" class="btn btn-primary">Update tokens -1</button>
                </div>
            </div>
            
            <div>
                <h3 style="text-align: center;">Provisional</h3>
                <form class="form-inline" @submit.prevent="handleFormSubmission()">
                  <button type="submit" class="btn btn-primary">Update tokens</button>
                  <div class="form-group" style="max-width: 250px;">
                    <input type="number" step="1" class="form-control" placeholder="Enter a number" style="max-width: 250px;" v-model.number="formInputNum">
                  </div>
                </form>
            </div>
            
            <div style="min-width: 200px; display: flex; flex-direction: column; margin-bottom: 16px;">
                <h5 style="text-align: center;">Deviation</h5>
                <div style="text-align: center;">
                    <button @click="incrementTotal(1)" type="button" class="btn btn-primary">Update tokens +1</button>
                </div>
            </div>
        </div>
      
        <div class="row" style="display: flex; justify-content: space-between;">
            <div style="min-width: 200px;">
                <div>
                    <div class="list-group">
                         <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your tokens:</div>
                                <div>{{yourTotal - 1}}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your cost:</div>
                                <div>{{ Math.round(decreased[playerId]) }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ Math.round(arrSum(decreased)) }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrSum(totals) - 1 }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        
        
            <div style="min-width: 350px;">
                <div>
                    <div class="list-group">
                        <div class="list-group-item">
                            <div style="display: flex; justify-content: space-between;">
                                <div><b>Your Tokens:</b></div>
                                <div><b>{{provisionalTotals[playerId]}}</b></div>
                            </div>
                        </div>
                        <div class="list-group-item">
                            <div style="display: flex; justify-content: space-between;">
                                <div><b>Your cost:</b></div>
                                <div><b>{{ Math.round(provisional[playerId] | 0)}}</b></div>
                            </div>
                        </div>
                        <div class="list-group-item">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ Math.round(arrSum(provisional) | 0) }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrSum(totals) }}</div>
                            </div>
                        </div>  
                    </div>
                </div>
            </div>
            
            <div style="min-width: 200px;">
                <div>            
                    <div class="list-group">
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your tokens:</div>
                                <div>{{ yourTotal + 1 }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Your cost:</div>
                                <div>{{ Math.round(increased[playerId]) }}</div>
                            </div>
                        </div>
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total cost:</div>
                                <div>{{ Math.round(arrSum(increased)) }}</div>
                            </div>
                        </div>              
                        <div class="list-group-item list-group-item-secondary">
                            <div style="display: flex; justify-content: space-between;">
                                <div>Total tokens:</div>
                                <div>{{ arrSum(totals) + 1}}</div>
                            </div>
                        </div> 
                    </div> 
                </div>
            </div>
        </div>
<!--        <br>-->
<!--        <br>-->
<!--        <br>-->
<!--        <div class="row">-->
<!--            <div class="col-md-12 card bg-light">-->
<!--                <div class="card-body">-->
<!--                    <div class="input-group" style="margin: auto;">-->
<!--                        <div class="input-group-prepend">-->
<!--                            <label class="input-group-text" for="inputGroupSelect01">Your tokens</label>-->
<!--                        </div>-->
<!--                        <select v-model.number="numberTokens" @change="inputChange()" :disabled="submitted" id="willingnessId" class="custom-select" autofocus>-->
<!--                            <option v-for="x in paymentOptions + 1" :value="x - (paymentOptions/2) - 1">{{ x - (paymentOptions/2) - 1 }}</option>-->
<!--                        </select>-->
<!--                    </div>-->
<!--                </div>-->
<!--            </div>-->
<!--        </div>    -->
      </div>
      `
}
