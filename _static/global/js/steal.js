let stealGameComponent = {
    components: {
        'probability-bar-component': probabilityBarComponent,
    },
    props: {
        maps: Array,
        groupPlayerId: Number,
        playerLocation: Object,
        investigationCount: Number,
        defendTokenTotal: Number,
        probCulprit: Number,
        probInnocent: Number,
        policeLogMessages: Array,
        mapSize: Number,
        stealLocation: Number,
        activeSteal: Number,
        activeStealMaps: Object,
        fineNotification: String,
    },
    data: function () {
        return {
            location: null,
            locationx: 0,
            locationy: 0,
        }
    },
    mounted: function () {
        console.log('FINE NOTIFICATION', this.fineNotification)
        let that = this;
        let selector = '#location'
        Draggable.create(selector, {
            minimumMovement: .01,
            bounds: that.$refs.stealcontainer,
            onDragStart: function () {
                that.locationDragStart(this)
            },
            onDragEnd: function () {
                that.checkLocation(this)
            },
        });

    },
    methods: {
        setStealLocation: function () {
            if (this.stealLocation === 1) {
                gsap.to('#location', 0, {x: 0, y: 0});
                return; // already starts in first steal location
            }

            let start = this.$refs['steallocation1'].getBoundingClientRect();
            let dest = this.$refs['steallocation' + this.stealLocation][0].getBoundingClientRect();

            gsap.to('#location', 0, {x: dest.x - start.x, y: dest.y - start.y});
        },
        locationDragStart: function (that) {
            // check the current location to see if we need to update api
            this.$emit('location-drag', {x: this.locationx, y: this.locationy, map: 0});
        },
        checkLocation: function (that) {
            if (that.hitTest(this.$refs.htarget, '10%')) {
                //location-center
                if (that.hitTest(this.$refs.prop2, '.000001%') && this.groupPlayerId != 2) {
                    let map = document.getElementById('prop2').getBoundingClientRect()
                    this.calculateLocation(map, 2);
                } else if (that.hitTest(this.$refs.prop3, '.000001%') && this.groupPlayerId != 3) {
                    let map = document.getElementById('prop3').getBoundingClientRect()
                    this.calculateLocation(map, 3);
                } else if (that.hitTest(this.$refs.prop4, '.000001%') && this.groupPlayerId != 4) {
                    let map = document.getElementById('prop4').getBoundingClientRect()
                    this.calculateLocation(map, 4);
                } else if (that.hitTest(this.$refs.prop5, '.000001%') && this.groupPlayerId != 5) {
                    let map = document.getElementById('prop5').getBoundingClientRect()
                    this.calculateLocation(map, 5);
                } else if (that.hitTest(this.$refs.prop6, '.000001%') && this.groupPlayerId != 6) {
                    let map = document.getElementById('prop6').getBoundingClientRect()
                    this.calculateLocation(map, 6);
                }
                else {
                    this.setStealLocation()
                    this.$emit('location-token-reset', this.randomLocation())
                }
            } else {
                this.setStealLocation()
                this.$emit('location-token-reset', this.randomLocation())
            }
        },
        calculateLocation(map, map_id) {  // prop_id is more like the player_id
            let location = this.$refs.location.getBoundingClientRect()
            this.locationx = location.x - map.x + 2 - 1; // + radius - border
            this.locationy = location.y - map.y + 2 - 1;

            if (0 <= this.locationx &&
                this.locationx <= this.mapSize &&
                0 <= this.locationy &&
                this.locationy <= this.mapSize
            ) {
                this.$emit('location-update', {x: this.locationx, y: this.locationy, map: map_id});
            } else {
                gsap.to('#location', 0, {x: 0, y: 0, ease: Back.easeOut});
            }
        },
        indicatorColor(map) {
            if (this.groupPlayerId == map) {
                return 'red'
            } else {
                return 'black'
            }
        },
        randomLocation: function () {
            return Math.floor(Math.random() * 9) + 1
        }
    },
    watch: {
        stealLocation: function () {
            this.setStealLocation();
        }
    },
    template:
        `
      <div class="steal" style="display:flex; flex-wrap: wrap">
        <div class="game">
            <div id="steal-container" class="upper" ref="stealcontainer">
                <div class='title'>Civilian Maps</div> 
                    <div ref='htarget' class="maps-container">
                      <div v-for="map in maps" class="map-container">
                            <div
                                class="map"
                                v-bind:style="{ height: mapSize + 'px', width: mapSize + 'px', background: (groupPlayerId==map+1 ? (activeStealMaps[groupPlayerId] > 0 ? 'rgba(224,53,49,' + activeStealMaps[groupPlayerId] * .25 + ')' : 'darkgrey') : (map+1 == activeSteal ? 'rgba(81,179,100,.5)' : 'white'))}" 
                                v-bind:player-id="(map+1)" 
                                :id='"prop" + (map+1)' 
                                :ref='"prop" + (map+1)'>
                                <div id="fine-notification" v-if="groupPlayerId==map+1" style="text-align: center; font-size: 50px; padding-top: 40px;">
                                    {{fineNotification}}
                                </div>
                                <!-- svg indicator id format: map-player-->
                                <svg v-for="player_id in 5" :key="player_id" :id="'indicator-' + (map+1) + '-' + (player_id + 1)" class="indicator" width="4" height="4">
                                  <circle cx="2" cy="2" r="2" :fill="indicatorColor(player_id+1)" />
                                </svg>
                            </div>
                            <div class="map-label">{{map+1 == groupPlayerId ? 'You' : 'Civilian ' + (map+1)}}</div>
                      </div>
                    </div>
                    <div class="token-container">
                        <div class="steal-locations-container">
                            <div class="steal-token" ref="steallocation1" id="steallocation1">
                                <svg id="location" height="21" width="21">
                                    <line x1="0" y1="0" x2="21" y2="21" style="stroke:red;stroke-width:3;"/>       
                                    <line x1="21" y1="0" x2="0" y2="21" style="stroke:red;stroke-width:3;"/>       
                                        
                                    <circle ref="location" cx="10.5" cy="10.5" r="2" fill="black" />
                                    Sorry, your browser does not support inline SVG.  
                                </svg> 
                            </div>
<!--                            todo: make right number of locations here-->
                            <div v-for="i in 8" class="steal-location" :ref='"steallocation" + (i+1)' :id='"steallocation" + (i+1)'>
                            </div>
                        </div>
                      <br>
<!--                      <div>-->
<!--                          location: {{location}}-->
<!--                          x: {{locationx}}-->
<!--                          y: {{locationy}}-->
<!--                      </div>-->
                      <div>
                    </div>
              </div>
            <div class="lower" style="display:flex;">
                <div class="investigation-data-container">
                    <div class="title">Investigating</div>
                    <div>
                        <div class="title-small">Officer tokens on investigate: <strong>{{investigationCount}}/{{defendTokenTotal}}</strong></div>
                        <br>
                        <probability-bar-component label="Probability fined if innocent" :percent=probInnocent></probability-bar-component>
                        <probability-bar-component label="Probability fined if culprit" :percent=probCulprit></probability-bar-component>  
                    </div>                  
                </div>
            </div>
        </div>
      </div>
      </div>
      `
}