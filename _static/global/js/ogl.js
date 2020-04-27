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
        }
    },
    created: function() {
        this.paymentOptions = this.paymentMax * 2;
    },
    mounted: function () {

    },
    methods: {
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
            if (this.method !== 1) { // todo: make this more obvious so we don't forget about it and break something
                return 0;
            }
            let thetaResults = {}
            let total = this.arrSum(this.totals)
            for(const pid in this.provisionalTotals) {
                let x = 0;
                let playerId2 = parseInt(pid)

                let tempTotal = total + direction
                tempTotal -= this.provisionalTotals[playerId2]

                for(const pid2 in this.provisionalTotals) {
                    if (pid2 === pid)
                        continue;

                    let ptotal = this.provisionalTotals[parseInt(pid2)]
                    if (this.playerId === pid2) {
                        ptotal += direction
                    }

                    xxx = Math.pow(ptotal - (1 / (this.smallN - 1)) * (tempTotal),2)
                    console.log(xxx)

                    x += xxx
                    console.log('?')
                }

                console.log('end of theta calculation')

                thetaResults[parseInt(pid)] = (this.gamma / 2) * (1 / (this.smallN - 2)) * x;

            }
            return thetaResults
        },
        calculateOgl: function(direction) {
            // the direction is +- 1.
            let thetas = this.calculateThetas(direction)
            if (direction === 0)
                console.log('thetas: ', thetas)
            let oglResults = {}

            let total = this.arrSum(this.provisionalTotals)
            if (direction !== 0) {
                total += direction;
            }
            for(let id in this.provisionalTotals) {
                let pid = parseInt(id)

                let ptotal = this.provisionalTotals[pid]
                if (pid === this.playerId) {
                    ptotal += direction
                }

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
        <div class="row">
            player_id: {{playerId}}
        </div>
        <div class="row">
            server costs: {{ provisionalCosts }}
        </div>
        <div class="row">
            local costs: {{ provisional }}    
        </div>
        <div class="row">
            server totals: {{ provisionalTotals }}    
        </div>
        <div class="row">
            local totals: {{ totals }}    
        </div>
        <div class="row">
            <div class="col-md-5 card bg-light">
                <div class="card-body">
                    <div class="input-group">
                      <div class="input-group-prepend">
                        <label class="input-group-text" for="inputGroupSelect01">Your tokens</label>
                      </div>
                        <select v-model.number="numberTokens" @change="inputChange()" :disabled="submitted" id="willingnessId" class="custom-select">
                            <option v-for="x in paymentOptions + 1" :value="x - (paymentOptions/2) - 1">{{ x - (paymentOptions/2) - 1 }}</option>
                        </select>
                    </div>
                </div>
            </div>
        
            <div class="col-md-7">
                <h5 style="text-align: center;">Provisional</h5>
                <div class="list-group">
                    <div class="list-group-item">
                        Your cost: {{ Math.round(provisional[playerId]) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>
                    <div class="list-group-item">
                        Total cost {{ Math.round(arrSum(provisional)) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>              
                    <div class="list-group-item">
                        Total tokens: {{ arrSum(totals) }}
                    </div>  
                </div>
                <br>
                <h5 style="text-align: center;">Deviations</h5>
                
                <div class="list-group">
                    <div class="list-group-item list-group-item-secondary">
                        +1 token
                    </div>
                    <div class="list-group-item">
                        Your cost: {{ Math.round(increased[playerId]) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>
                    <div class="list-group-item">
                        Total cost {{ Math.round(arrSum(increased)) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>              
                    <div class="list-group-item">
                        Total tokens: {{ arrSum(totals) + 1}}
                    </div> 
                </div> 
                <br>
                <div class="list-group">
                     <div class="list-group-item list-group-item-secondary">
                        -1 token
                    </div>
                    <div class="list-group-item">
                        Your cost: {{ Math.round(decreased[playerId]) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>
                    <div class="list-group-item">
                        Total cost {{ Math.round(arrSum(decreased)) }} (<img src="https://i.imgur.com/BQXgE3F.png" alt="grain" style="height: 20px;">)
                    </div>              
                    <div class="list-group-item">
                        Total tokens: {{ arrSum(totals) - 1 }}
                    </div>
                </div>
            </div>
        </div>    
      </div>
      `
}
