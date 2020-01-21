let harvestItemsComponent = {
    props: {
        harvestStatus: Number,
    },
    data: function () {
        return {
            items: ['plow', 'seed', 'water', 'harvest'], // todo: add none here for when nothing has been done or the user just dragged the harvest item successfully
            lastCompleted: null,
        }
    },
    mounted: function () {
        for (let i = 0; i < this.items.length; i++) {
            let that = this;
            Draggable.create("#" + this.items[i], {
                bounds: document.getElementById("harvestGame"),
                onDragEnd: function () {
                    that.checkLocation(this)
                },
            });
        }
    },
    methods: {
        checkLocation: function (that, id) {
            let index = that.target.attributes.index.value;
            if (index == this.harvestStatus && that.hitTest(this.$refs.htarget, '100%')) {
                //hide item and move it back to start
                let tl = gsap.timeline({onComplete: this.updateHarvestStatus});
                tl.to(that.target, 0, {autoAlpha: 0});
                tl.to(that.target, {x: 0, y: 0});

            } else {
                gsap.to(that.target, 0, {x: 0, y: 0, ease: Back.easeOut});
            }
        },
        updateHarvestStatus() {
            this.$emit('harvest-update', this.harvestStatus,);
        }
    },
    template: `
  
      <div id="harvest-container" class="game">
        <div class="upper-harvest">
            <div class='harvest-items'>
              <div v-for='(i, index) in items' :id='i' :index='index' :ref='i' class='harvest-item'>
                {{i}}
                <img :src="'/static/global/images/' + i + '.png'" style="width: 50%; height: 50%"/>
              </div>
            </div>
        </div>
        <div class="lower" ref='htarget'> 
            <div class="harvest-complete-items">
              <div class="harvest-complete-container">
                <div class='harvest-complete-item' v-for='(i, index) in 3'>
                  <img v-if="harvestStatus > 0" :src="'/static/global/images/harvest' + (harvestStatus+1) + '.png'" style="width: 50%; height: 50%"/>
                </div>
              </div>
              <div class="harvest-complete-container">
                <div class='harvest-complete-item' v-for='(i, index) in 3'>
                  <img v-if="harvestStatus > 0" :src="'/static/global/images/harvest' + (harvestStatus+1) + '.png'" style="width: 50%; height: 50%"/>
                </div>
              </div>  
            </div>
        </div>
      </div>
    `
}