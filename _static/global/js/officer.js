let probabilityBarComponent = {
    props: {
        label: String,
        percent: Number,
    },
    data: function () {
        return {
            defenseTokens: []
        }
    },
    template:
        `
        <div>
            <div class="title-small">{{ label }}: <strong>{{percent}}%</strong></div>
            <div class='bar'>
                <div class="innocent" :style="{'width':(percent+'%')}">
                </div>
            </div>
        </div>
        `
}

let officerGameComponent = {
    components: {
        'probability-bar-component': probabilityBarComponent,
    },
    props: {
        maps: Array,
        officerUnits: Array,
        officerIncome: Number,
        groupPlayerId: Number,
        investigationCount: Number,
        defendTokenTotal: Number,
        policeLogMessages: Array,
        mapSize: Number,
        defendTokenSize: Number,
        probabilityReprimand: Number,
        reprimandAmount: Number,
    },
    data: function () {
        return {
            playerId: Number,
            locationx: String,
            locationy: String,
            map: String,
            tokenStatuses: []
        }
    },
    created: function () {
        this.locationx = '';
        this.locationy = '';
        this.map = '';
    },
    mounted: function () {
        for (let i = 0; i < this.officerUnits.length; i++) {
            let oGame = document.getElementById("officerGame");
            let that = this;
            let drag = Draggable.create("#unit" + i, {
                minimumMovement: .01,
                bounds: document.getElementById("officerGame"), //todo add ref stuff after vuex is implemented
                onDragStart: function () {
                    that.tokenDragStart(this, that.officerUnits[i])
                },
                onDragEnd: function () {
                    that.checkLocation(this, that.officerUnits[i])
                },
            });
            this.tokenStatuses.push(drag);
            // this.disableToken(drag);
        }
    },
    methods: {
        disableToken: function(id) {
            let selector = "#unit" + id
            let dragToken = Draggable.get(selector)
            dragToken.disable();
            // gsap.to(selector, {background: 'red'});
            setTimeout(() => {
                dragToken.enable()
            }, 1000)
        },
        tokenDragStart: function (that, item) {
            // console.log(item)
            this.$emit('token-drag', item);
            // // update api with unit location
            // this.updateOfficerToken(item);
        },
        checkLocation: function (that, item) {
            if (that.hitTest(this.$refs.officerGame, '100%')) {
                //location-center
                if (that.hitTest(this.$refs.map6, '1%')) {
                    this.map = 6;
                    item.map = 6;
                    let map = document.getElementById('map6').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map5, '1%')) {
                    this.map = 5;
                    item.map = 5;
                    let map = document.getElementById('map5').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map2, '.000001%')) {
                    this.map = 2;
                    item.map = 2;
                    let map = document.getElementById('map2').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map3, '.000001%')) {
                    this.map = 3;
                    item.map = 3;
                    let map = document.getElementById('map3').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.map4, '.000001%')) {
                    this.map = 4;
                    item.map = 4;
                    let map = document.getElementById('map4').getBoundingClientRect()
                    this.calculateLocation(map, that, item);
                } else if (that.hitTest(this.$refs.investigationcontainer, '100%')) {
                    item.map = 11;
                    this.$emit('investigation-update', item)
                } else {
                    gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
                    this.$emit('defense-token-reset', item.number)
                }
            } else {
                gsap.to(that.target, 0.5, {x: 0, y: 0, ease: Back.easeOut});
                this.$emit('defense-token-reset', item.number)
            }
        },
        calculateLocation: function(map, unitContext, item) {
            let unit = unitContext.target.getBoundingClientRect()
            this.locationy = unit.y - map.y - 1;
            this.locationx = unit.x - map.x - 1;
            item.x = this.locationx;
            item.y = this.locationy;
            this.disableToken(item.number-1)
            // update api with unit location
            this.updateOfficerToken(item);
        },
        updateOfficerToken: function(item) {
            // console.log('item: ', item);
            this.$emit('token-update', item);
        }
    },
    template:
        `
          <div ref="officerGame">
              <div class="upper">      
                <div class='title'>Civilian Maps</div> 
                <div class="maps-container">
                    <div v-for="map in maps" v-bind:player-id="(map+1)" :id='"map" + (map+1)' :ref='"map" + (map+1)' class="map-container">
                      <div class="map other" :id='"map" + (map+1)' :ref='"map" + (map+1)' v-bind:style="{ height: mapSize + 'px', width: mapSize + 'px' }">
                            <div v-for="player_id in 5" class="intersection-label" :id="'intersection-label-' + (map+1) + '-' + (player_id + 1)" >
                                -1
                            </div>
                            <svg v-for="player_id in 5" :key="player_id" :id="'indicator-' + (map+1) + '-' + (player_id + 1)" class="indicator" width="6" height="6">
                                <circle cx="3" cy="3" r="2" fill="black" />
                            </svg>
                      </div>
                      <div class="map-label">
                        Civilian {{map+1}}
                      </div>
                    </div>
                </div>
                <div class="token-container">
                    <div style="margin: 10px">
                        <div class="title-small officer-info-container">
                            <div class="title-small data-row">
                                <div class="left">Amount earned per arrest: </div>
                                <div class="right" style="color: green; font-weight: bold;"><div class="number-right-align">{{officerIncome}}</div></div>
                            </div>
                        </div>
                        <div style="clear: both;"></div>
                    </div>
                    <div class="officer-units" style="display:flex;">
                        <div v-for="(unit, index) in officerUnits" :id="'unit'+index" class="officer-unit" v-bind:style="{ height: defendTokenSize + 'px', width: defendTokenSize + 'px' }" :ref='"unit" + unit'>
                        </div>
                    </div>
                    
                    <div class="officer-info-container">
                        <div class="title-small data-row">
                            <div class="left">Amount lost per reprimand: </div>
                            <div class="right" style="color: red; font-weight: bold;"><div class="number-right-align">{{reprimandAmount}}</div></div>
                        </div>
                        <div style="clear: both;"></div>
                        <div class="title-small data-row">
                            <div class="left">Probability of reprimand: </div>
                            <div class="right" style="color: red; font-weight: bold;"><div class="number-right-align">{{probabilityReprimand}}%</div></div>
                        </div>
                    </div>
                </div>
                <div class="investigation-data-container">
                    <div class="title">Investigation Map</div>
                    <div id="officer-investigation-container" ref='investigationcontainer' v-bind:style="{ height: mapSize + 'px' }"></div>
                </div>
              </div>
          </div>
      `
}